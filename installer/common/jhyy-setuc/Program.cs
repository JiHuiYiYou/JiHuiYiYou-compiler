// installer/common/jhyy-setuc/Program.cs
//
// v1.8.2 patch tool: register JHYY.EditInVSCode custom ProgId + write
// UserChoice Hash via Mozilla's reverse-engineered algorithm.
//
// v1.8.3 patch: adds --system-context mode for MSI CustomAction use.
//   SYSTEM trust chain bypasses UCPD.sys (Win10 2024-02+) — no need to
//   stop UCPD. Enumerates HKEY_USERS S-1-5-21-… SIDs and writes each
//   user's UserChoice directly. See docs/internal/workarounds.md W-062.
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
// Usage (single-user, admin from interactive session — v1.8.2 path):
//   jhyy-setuc.exe <ext> <progId> <description> <iconPath> <iconIndex> <openExe> [openArg]
//     openExe = full exe path (no quotes needed in CLI — C# adds them)
//     openArg = optional arg template (default "%1")
//
// Usage (multi-user, SYSTEM context via MSI CustomAction — v1.8.3 path):
//   jhyy-setuc.exe --system-context <ext> <progId>
//     Enumerates HKEY_USERS S-1-5-21-… SIDs, writes each user's UserChoice.
//     SYSTEM token bypasses UCPD kernel filter — does NOT stop UCPD.
//
// Behavior (single-user, v1.8.2):
//   1. Registers ProgId at HKCU\Software\Classes\<progId> with DefaultIcon + shell\open\command
//   2. Sets ApplicationAssociationToasts\<progId>_<ext> = 0 (per PS-SFTA — required for Windows)
//   3. STOPS UCPD service (admin required) so the next UserChoice write isn't blocked
//   4. Removes conflicting OpenWithProgids entries (VSCode shadow), keeps our ProgId
//   5. Deletes existing UserChoice (Windows shell + VSCode may have re-registered it)
//   6. Computes Mozilla-style Hash for (ext, ProgId, current minute timestamp)
//   7. Writes UserChoice ProgId + Hash
//   8. ALWAYS restarts UCPD in finally block (even on exception)
//
// Behavior (multi-user SYSTEM context, v1.8.3):
//   1. Enumerates HKEY_USERS S-1-5-21-… SIDs (skips SYSTEM / LocalService / NetworkService / _Classes)
//   2. For each user SID: compute Mozilla Hash with that SID, write
//      HKEY_USERS\<SID>\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\<ext>\UserChoice
//   3. Per-user failures are logged but do NOT abort the loop (partial success OK)
//
// Exit codes:
//   0 = success (single-user path, OR all users succeeded in multi-user path)
//   1 = wrong args / usage error
//   2 = UCPD.sys blocked UserChoice write (single-user), OR one or more users failed (multi-user)

using System;
using System.Collections.Generic;
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

        static string ComputeHashWithSid(string ext, string progId, string sid) {
            // v1.8.3: caller supplies the target user SID — used by system-context
            // path where we enumerate HKEY_USERS and write per-user UserChoice.
            string input = FormatUserChoiceString(ext, sid, progId, DateTime.Now);
            return HashString(input);
        }

        static int StopUcpd() {
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
                return p.ExitCode;
            } catch (Exception ex) {
                Console.WriteLine($"[v1.8.2 Path B] sc stop failed: {ex.Message}");
                return -1;
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
            int stopUcpdExit = StopUcpd();

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

                try {
                    using (var uc = Registry.CurrentUser.CreateSubKey(userChoicePath, true)) {
                        uc.SetValue("ProgId", progId, RegistryValueKind.String);
                        uc.SetValue("Hash", hash, RegistryValueKind.String);
                        Console.WriteLine($"[v1.8.2 Path B] Wrote UserChoice: ProgId={progId}, Hash={hash}");
                    }
                } catch (UnauthorizedAccessException ex) {
                    Console.Error.WriteLine($"[v1.8.2 Path B] UCPD.sys blocked UserChoice write: {ex.Message}");
                    Console.Error.WriteLine($"[v1.8.2 Path B] Win10 Feb 2024+ UCPD.sys kernel filter blocks all non-Windows-shell UserChoice writes.");
                    Console.Error.WriteLine($"[v1.8.2 Path B] sc.exe stop UCPD returned: {stopUcpdExit} (access denied even as admin).");
                    Console.Error.WriteLine($"[v1.8.2 Path B] Manual fix: 右键 .jhyy 文件 → 打开方式 → 选择其他应用 → JHYY Source File → 勾选 始终用此应用");
                    Console.Error.WriteLine($"[v1.8.2 Path B] OR: 安全模式启动 → reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\UCPD /v Start /t REG_DWORD /d 4 /f → 重启 → 重跑此脚本");
                    return 2;
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

        // v1.8.3: MSI CustomAction entry path. Runs under SYSTEM context (Impersonate="no").
        // Enumerates HKEY_USERS S-1-5-21-… SIDs and writes each user's UserChoice directly.
        // SYSTEM token bypasses UCPD.sys kernel filter — no StopUcpd/StartUcpd needed.
        //
        // Caller is responsible for:
        //   - Registering ProgId at HKLM\Software\Classes\<progId> (perMachine install via MSI)
        //   - Setting ApplicationAssociationToasts at HKLM (perMachine) OR per-user via this same loop
        //
        // Per-user UserChoice is the BLOCKING point on Win10 2024-02+: every interactive user
        // must have their own HKEY_USERS\<SID>\…\UserChoice entry or Explorer falls back to
        // whatever the SYSTEM / HKLM cascade says (typically Code.exe for .jhyy).
        //
        // Returns 0 if all enumerated users succeeded, 2 if any user failed (partial OK),
        // 2 if no interactive users were found (unusual — fresh-install Win10 without
        // any user profile created yet).
        public static int ApplyPathBSystemContext(string ext, string progId) {
            Console.WriteLine($"[v1.8.3 system-context] ext={ext} progId={progId}");

            // Enumerate HKEY_USERS — each subkey is a SID string (e.g. "S-1-5-21-...-1001")
            // or a "_Classes" mirror (e.g. "S-1-5-21-...-1001_Classes").
            using var users = Registry.Users;
            string[] sidNames = users.GetSubKeyNames();

            int totalUsers = 0;
            int successUsers = 0;
            int failedUsers = 0;
            var failedSids = new List<string>();
            var skippedSids = new List<string>();

            foreach (string sid in sidNames) {
                // Filter to interactive-user SIDs only.
                // - S-1-5-18 SYSTEM / S-1-5-19 LocalService / S-1-5-20 NetworkService: not users
                // - "_Classes" mirrors: HKCU\Software\Classes — auto-skip
                // - "DEFAULT" / "WDI" etc: legacy / system, skip
                if (!sid.StartsWith("S-1-5-21-")) {
                    skippedSids.Add(sid);
                    continue;
                }
                if (sid.EndsWith("_Classes")) {
                    skippedSids.Add(sid);
                    continue;
                }

                totalUsers++;
                try {
                    // Per-user toast suppression (ApplicationAssociationToasts\<progId>_<ext> = 0).
                    // PS-SFTA requirement: Windows won't show "Choose default app" popup if this
                    // is set. Without it, first double-click may revert UserChoice.
                    try {
                        string toastPath = sid + @"\Software\Microsoft\Windows\CurrentVersion\ApplicationAssociationToasts";
                        using (var toastKey = Registry.Users.CreateSubKey(toastPath, true)) {
                            toastKey.SetValue(progId + "_" + ext, 0, RegistryValueKind.DWord);
                        }
                    } catch (Exception tex) {
                        // Toast write is best-effort — log but don't fail this user
                        Console.Error.WriteLine($"[v1.8.3 system-context] SID={sid} toast: {tex.Message}");
                    }

                    // Compute Mozilla Hash with the TARGET user's SID — critical: the hash
                    // includes SID in input, so SYSTEM's S-1-5-18 hash would be rejected
                    // by Explorer reading from a user's HKCU.
                    string hash = ComputeHashWithSid(ext, progId, sid);

                    // Write UserChoice directly into the target user's hive.
                    string ucPath = sid + @"\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\" + ext + @"\UserChoice";
                    using (var uc = Registry.Users.CreateSubKey(ucPath, true)) {
                        uc.SetValue("ProgId", progId, RegistryValueKind.String);
                        uc.SetValue("Hash", hash, RegistryValueKind.String);
                    }
                    Console.WriteLine($"[v1.8.3 system-context] SID={sid} ProgId={progId} Hash={hash}");
                    successUsers++;
                } catch (Exception ex) {
                    Console.Error.WriteLine($"[v1.8.3 system-context] SID={sid} FAILED: {ex.Message}");
                    failedSids.Add(sid);
                    failedUsers++;
                    // continue — partial success is acceptable per plan § Phase 1
                }
            }

            Console.WriteLine($"[v1.8.3 system-context] summary: total={totalUsers} success={successUsers} failed={failedUsers} skipped={skippedSids.Count}");
            if (skippedSids.Count > 0 && totalUsers == 0) {
                Console.Error.WriteLine($"[v1.8.3 system-context] no interactive user SIDs found — only saw: {string.Join(", ", skippedSids)}");
            }
            if (failedSids.Count > 0) {
                Console.Error.WriteLine($"[v1.8.3 system-context] failed SIDs: {string.Join(", ", failedSids)}");
            }

            if (totalUsers == 0) {
                Console.Error.WriteLine("[v1.8.3 system-context] no interactive users — registry unchanged");
                return 2;
            }

            // v1.8.3 sentinel: on full success (all users succeeded), write
            // HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied so
            // install-configure-all.bat RunOnce step 6 can skip the redundant
            // user-context manual-fix-icon-cache.ps1 invocation. Sentinel is
            // HKLM so the per-user RunOnce can read it.
            //
            // Sentinel is intentionally NOT written on partial success — those
            // users still benefit from the RunOnce fallback.
            if (failedUsers == 0 && totalUsers > 0) {
                try {
                    using var sentinel = Registry.LocalMachine.CreateSubKey(@"SOFTWARE\JiHuiYiYou\JHYY", true);
                    sentinel.SetValue("UserChoiceSystemContextApplied", DateTime.UtcNow.ToString("o"), RegistryValueKind.String);
                    Console.WriteLine("[v1.8.3 system-context] sentinel: wrote HKLM\\SOFTWARE\\JiHuiYiYou\\JHYY\\UserChoiceSystemContextApplied");
                } catch (Exception ex) {
                    // Sentinel write is best-effort — failure here doesn't change
                    // the per-user UserChoice outcome. Log + continue.
                    Console.Error.WriteLine($"[v1.8.3 system-context] sentinel write failed: {ex.Message}");
                }
            }

            return failedUsers > 0 ? 2 : 0;
        }
    }

    class Program {
        // CLI (single-user, v1.8.2):
        //   jhyy-setuc.exe <ext> <progId> <description> <iconPath> <iconIndex> <openExe> [openArg]
        //   openExe = full path to exe (e.g. Code.exe) — no quotes needed in CLI
        //   openArg = optional arg template (default "%1") — C# builds the full shell command
        //
        // CLI (multi-user SYSTEM context, v1.8.3):
        //   jhyy-setuc.exe --system-context <ext> <progId>
        //
        // We split exe + arg so PowerShell's Start-Process -ArgumentList array doesn't have
        // to deal with embedded quotes (which Windows' CommandLineToArgvW strips, splitting
        // a single arg into 2 — see v1.8.2 bug history).
        static int Main(string[] args) {
            // v1.8.3: detect --system-context flag, dispatch to multi-user path
            if (args.Length >= 1 && args[0] == "--system-context") {
                if (args.Length != 3) {
                    Console.Error.WriteLine("Usage: jhyy-setuc.exe --system-context <ext> <progId>");
                    return 1;
                }
                return UC.ApplyPathBSystemContext(args[1], args[2]);
            }

            if (args.Length < 6 || args.Length > 7) {
                Console.Error.WriteLine("Usage: jhyy-setuc.exe [--system-context <ext> <progId>] | <ext> <progId> <description> <iconPath> <iconIndex> <openExe> [openArg]");
                return 1;
            }
            string ext = args[0];
            string progId = args[1];
            string desc = args[2];
            string icon = args[3];
            int iconIdx = int.Parse(args[4]);
            string openExe = args[5];
            string openArg = args.Length >= 7 ? args[6] : "%1";
            // Build full shell\open\command value: "exe" "arg"
            string cmd = "\"" + openExe + "\" \"" + openArg + "\"";
            return UC.ApplyPathB(ext, progId, desc, icon, iconIdx, cmd);
        }
    }
}