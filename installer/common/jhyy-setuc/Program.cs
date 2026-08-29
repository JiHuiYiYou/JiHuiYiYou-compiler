// installer/common/jhyy-setuc/Program.cs
//
// v1.8.2 patch tool: register JHYY.EditInVSCode custom ProgId + write
// UserChoice Hash via Mozilla's reverse-engineered algorithm.
//
// Algorithm reference:
//   Mozilla Firefox browser/components/shell/WindowsUserChoice.cpp
//   (Apache 2.0 / Mozilla Public License 2.0)
//   Originally based on PS-SFTA by DanysysTeam / SetUserFTA by kolbi
//   (MIT License, https://github.com/DanysysTeam/PS-SFTA,
//    https://kolbi.cz/blog/2017/10/25/setuserfta-userchoice-hash-defeated)
//
// Algorithm: format input string "{ext}{sid}{progId}{fileTime.hi08lx}{fileTime.lo08lx}{userExperience}",
// lowercase, append null terminator, MD5-hash, use MD5[0]|1 / MD5[1]|1 as constant multipliers
// in a 2-DWORD block scramble loop. Base64-encode the resulting 8-byte hash.
//
// Usage:
//   jhyy-setuc.exe <ext> <progId> <description> <iconPath> <iconIndex> <openCommand>
//
// Behavior:
//   1. Registers ProgId at HKCU\Software\Classes\<progId> with DefaultIcon + shell\open\command
//   2. Sets ApplicationAssociationToasts\<progId>_<ext> = 0 (per PS-SFTA — required for Windows)
//   3. STOPS UCPD service (admin required) so the next UserChoice write isn't blocked
//   4. Removes conflicting OpenWithProgids entries (VSCode shadow), keeps our ProgId
//   5. Deletes existing UserChoice (Windows shell + VSCode may have re-registered it)
//   6. Computes Mozilla-style Hash for (ext, ProgId, current minute timestamp)
//   7. Writes UserChoice ProgId + Hash
//   8. ALWAYS restarts UCPD in finally block (even on exception)

using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Threading;
using Microsoft.Win32;

namespace JHYY.SetUC {
    public class UC {
        // Microsoft-internal UserExperience constant — see Mozilla's WindowsUserChoice.cpp
        const string UserExperience = "User Choice set via Windows User Experience {D18B6DD5-6124-4341-9318-804003BAFA0B}";

        static uint WordSwap(uint v) => (v >> 16) | (v << 16);

        static string GetUserSid() {
            using var identity = WindowsIdentity.GetCurrent();
            return identity.User.Value;
        }

        static string HashString(string input) {
            byte[] bytes = Encoding.Unicode.GetBytes(input);
            // Firefox source: (lstrlenW + 1) * sizeof(wchar_t) — INCLUDES null terminator
            byte[] withNull = new byte[bytes.Length + 2];
            Array.Copy(bytes, withNull, bytes.Length);
            bytes = withNull;
            int len = bytes.Length;
            if (len == 0) return null;

            using var md5 = MD5.Create();
            byte[] md5Hash = md5.ComputeHash(bytes);
            uint md5_0 = BitConverter.ToUInt32(md5Hash, 0);
            uint md5_1 = BitConverter.ToUInt32(md5Hash, 4);

            // Constants from Mozilla's WindowsUserChoice.cpp (Win10 1803+ / 20H2+)
            var C0s = new uint[2][] {
                new uint[] { md5_0 | 1u, 0xCF98B111u, 0x87085B9Fu, 0x12CEB96Du, 0x257E1D83u },
                new uint[] { md5_1 | 1u, 0xA27416F5u, 0xD38396FFu, 0x7C932B89u, 0xBFA49F69u }
            };
            var C1s = new uint[2][] {
                new uint[] { md5_0 | 1u, 0xEF0569FBu, 0x689B6B9Fu, 0x79F8A395u, 0xC3EFEA97u },
                new uint[] { md5_1 | 1u, 0xC31713DBu, 0xDDCD1F0Fu, 0x59C3AF2Du, 0x35BD1EC9u }
            };

            const int DWORDS_PER_BLOCK = 2;
            int blockCount = len / 8;
            if (blockCount == 0) return null;

            uint h0 = 0, h1 = 0, h0Acc = 0, h1Acc = 0;

            for (int i = 0; i < blockCount; i++) {
                for (int j = 0; j < DWORDS_PER_BLOCK; j++) {
                    uint[] C0 = C0s[j];
                    uint[] C1 = C1s[j];
                    uint inputDword = BitConverter.ToUInt32(bytes, (i * 2 + j) * 4);

                    h0 += inputDword;
                    h0 *= C0[0];
                    h0 = WordSwap(h0) * C0[1];
                    h0 = WordSwap(h0) * C0[2];
                    h0 = WordSwap(h0) * C0[3];
                    h0 = WordSwap(h0) * C0[4];
                    h0Acc += h0;

                    h1 += inputDword;
                    h1 = WordSwap(h1) * C1[1] + h1 * C1[0];
                    h1 = ((h1 >> 16) * C1[2]) + h1 * C1[3];
                    h1 = WordSwap(h1) * C1[4] + h1;
                    h1Acc += h1;
                }
            }

            uint[] result = new uint[] { h0 ^ h1, h0Acc ^ h1Acc };
            byte[] resultBytes = new byte[8];
            Array.Copy(BitConverter.GetBytes(result[0]), 0, resultBytes, 0, 4);
            Array.Copy(BitConverter.GetBytes(result[1]), 0, resultBytes, 4, 4);
            return Convert.ToBase64String(resultBytes);
        }

        static string FormatUserChoiceString(string ext, string sid, string progId, DateTime timestamp) {
            // Firefox source: zero out seconds + milliseconds before FILETIME conversion
            var ts = new DateTime(timestamp.Year, timestamp.Month, timestamp.Day,
                                  timestamp.Hour, timestamp.Minute, 0,
                                  DateTimeKind.Local);
            long fileTime = ts.ToFileTime();
            uint hi = (uint)(fileTime >> 32);
            uint lo = (uint)(fileTime & 0xFFFFFFFF);
            string s = ext + sid + progId + hi.ToString("x8") + lo.ToString("x8") + UserExperience;
            return s.ToLowerInvariant();
        }

        static string ComputeHash(string ext, string progId) {
            string sid = GetUserSid();
            string input = FormatUserChoiceString(ext, sid, progId, DateTime.Now);
            return HashString(input);
        }

        static void StopUcpd() {
            try {
                var psi = new ProcessStartInfo {
                    FileName = "sc.exe",
                    Arguments = "stop UCPD",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                using var p = Process.Start(psi);
                p.WaitForExit(10000);
                Console.WriteLine($"[v1.8.2 Path B] sc.exe stop UCPD: exit={p.ExitCode}");
                Thread.Sleep(1000);
            } catch (Exception ex) {
                Console.WriteLine($"[v1.8.2 Path B] sc stop failed: {ex.Message}");
            }
        }

        static void StartUcpd() {
            try {
                var psi = new ProcessStartInfo {
                    FileName = "sc.exe",
                    Arguments = "start UCPD",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                using var p = Process.Start(psi);
                p.WaitForExit(10000);
                Console.WriteLine($"[v1.8.2 Path B] sc.exe start UCPD: exit={p.ExitCode}");
            } catch (Exception ex) {
                Console.WriteLine($"[v1.8.2 Path B] sc start failed: {ex.Message}");
            }
        }

        public static int ApplyPathB(string ext, string progId, string progIdDescription,
                                      string iconPath, int iconIndex, string openCommand) {
            Console.WriteLine($"[v1.8.2 Path B] ext={ext} progId={progId}");

            // 1. Register custom ProgId at HKCU\Software\Classes\<progId>
            using (var classes = Registry.CurrentUser.OpenSubKey(@"Software\Classes", true)) {
                using (var progIdKey = classes.CreateSubKey(progId, true)) {
                    progIdKey.SetValue(null, progIdDescription);
                    using (var iconKey = progIdKey.CreateSubKey("DefaultIcon", true)) {
                        iconKey.SetValue(null, $"\"{iconPath}\",{iconIndex}");
                    }
                    using (var shellKey = progIdKey.CreateSubKey(@"shell\open\command", true)) {
                        shellKey.SetValue(null, openCommand);
                    }
                }
            }
            Console.WriteLine($"[v1.8.2 Path B] Registered ProgId {progId}");

            // 2. Set ApplicationAssociationToasts (per PS-SFTA — required for Windows to recognize ProgId)
            try {
                using var toastKey = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\ApplicationAssociationToasts", true);
                toastKey.SetValue(progId + "_" + ext, 0, RegistryValueKind.DWord);
                Console.WriteLine($"[v1.8.2 Path B] Set ApplicationAssociationToasts\\{progId}_{ext} = 0");
            } catch (Exception ex) {
                Console.WriteLine($"[v1.8.2 Path B] ApplicationAssociationToasts: {ex.Message}");
            }

            // 3. Stop UCPD to allow UserChoice write (admin required)
            Console.WriteLine("[v1.8.2 Path B] Stopping UCPD service...");
            StopUcpd();

            try {
                // 4. Clean OpenWithProgids — remove VSCode shadow, keep our ProgId
                string owpPath = @"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\" + ext + @"\OpenWithProgids";
                using (var owp = Registry.CurrentUser.OpenSubKey(owpPath, true)) {
                    if (owp != null) {
                        foreach (var sub in owp.GetSubKeyNames()) {
                            if (sub != progId) {
                                owp.DeleteSubKeyTree(sub, false);
                                Console.WriteLine($"[v1.8.2 Path B] Removed OpenWithProgids\\{sub}");
                            }
                        }
                    }
                }

                // 5. Delete old UserChoice (UCPD stopped, should succeed now)
                string userChoicePath = @"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\" + ext + @"\UserChoice";
                try {
                    Registry.CurrentUser.DeleteSubKeyTree(userChoicePath, false);
                    Console.WriteLine("[v1.8.2 Path B] Deleted old UserChoice");
                } catch (Exception ex) {
                    Console.WriteLine($"[v1.8.2 Path B] UserChoice delete: {ex.Message}");
                }

                // 6. Compute hash and write new UserChoice
                string hash = ComputeHash(ext, progId);
                Console.WriteLine($"[v1.8.2 Path B] Computed Hash: {hash}");

                using (var uc = Registry.CurrentUser.CreateSubKey(userChoicePath, true)) {
                    uc.SetValue("ProgId", progId, RegistryValueKind.String);
                    uc.SetValue("Hash", hash, RegistryValueKind.String);
                    Console.WriteLine($"[v1.8.2 Path B] Wrote UserChoice: ProgId={progId}, Hash={hash}");
                }

                // 7. Re-add ProgId to OpenWithProgids if missing
                using (var owp = Registry.CurrentUser.OpenSubKey(owpPath, true)) {
                    if (owp == null) {
                        using (var newOwp = Registry.CurrentUser.CreateSubKey(owpPath, true)) {
                            newOwp.CreateSubKey(progId, true);
                            Console.WriteLine($"[v1.8.2 Path B] Created OpenWithProgids\\{progId}");
                        }
                    } else if (Array.IndexOf(owp.GetSubKeyNames(), progId) < 0) {
                        owp.CreateSubKey(progId, true);
                        Console.WriteLine($"[v1.8.2 Path B] Added OpenWithProgids\\{progId}");
                    }
                }

                return 0;
            } finally {
                // 8. Always restart UCPD
                Console.WriteLine("[v1.8.2 Path B] Restarting UCPD service...");
                StartUcpd();
            }
        }
    }

    class Program {
        static int Main(string[] args) {
            if (args.Length != 6) {
                Console.Error.WriteLine("Usage: jhyy-setuc.exe <ext> <progId> <description> <iconPath> <iconIndex> <openCommand>");
                return 1;
            }
            string ext = args[0];
            string progId = args[1];
            string desc = args[2];
            string icon = args[3];
            int iconIdx = int.Parse(args[4]);
            string cmd = args[5];
            return UC.ApplyPathB(ext, progId, desc, icon, iconIdx, cmd);
        }
    }
}