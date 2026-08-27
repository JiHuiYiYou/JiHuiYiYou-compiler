// vscode-ext/src/extension.ts — JHYY language extension runtime
//
// v1.5.9: adds "Run JHYY File" play button via contributed command +
// menus.editor/title/run + Terminal.sendText (ms-python.python pattern).
// No tasks.json, no launch.json, no DAP — JHYY has no debugger.
//
// Commands:
//   jhyy.runFile      ▶  run `jhyy run <file>` (editor/title/run — Run area)
//   jhyy.compileOnly  🛠 run `jhyy build <file>` (editor/title — regular title bar)
//
// PATH probe (spawnSync --version) detects missing toolchain and surfaces
// a VS Code info notification with "Open Settings" affordance — falls back
// gracefully when jhyy.exe is not on PATH (per project memory
// project_jhyy_install_path: C:\Program Files\JHYY\bin needs manual add).

import * as vscode from 'vscode';
import { spawnSync } from 'child_process';

let jhyyTerminal: vscode.Terminal | undefined;

export function activate(context: vscode.ExtensionContext) {
    context.subscriptions.push(
        vscode.commands.registerCommand('jhyy.runFile',     () => runOrCompile('run')),
        vscode.commands.registerCommand('jhyy.compileOnly', () => runOrCompile('compile')),
    );
}

async function runOrCompile(mode: 'run' | 'compile'): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'jhyy') {
        return;
    }

    const cfg = vscode.workspace.getConfiguration('jhyy.run');
    const saveBeforeRun = cfg.get<boolean>('saveBeforeRun', true);
    const terminalName  = cfg.get<string>('terminalName', 'JHYY');
    const executorPath  = cfg.get<string>('executorPath', '');
    const executor      = cfg.get<string>('executor', 'jhyy run');

    if (saveBeforeRun && editor.document.isDirty) {
        try {
            const saved = await editor.document.save();
            if (!saved) {
                void vscode.window.showErrorMessage('JHYY: save failed, aborting run.');
                return;
            }
        } catch (e) {
            void vscode.window.showErrorMessage(`JHYY: save error: ${e}`);
            return;
        }
    }

    const probeTarget = executorPath.trim() || executor.split(/\s+/, 1)[0] || 'jhyy';
    const probe = spawnSync(probeTarget, ['--version'], {
        windowsHide: true,
        shell: false,
        timeout: 2000,
        stdio: 'ignore',
    });
    if (probe.error && (probe.error as NodeJS.ErrnoException).code === 'ENOENT') {
        const choice = await vscode.window.showInformationMessage(
            `JHYY 编译器未找到 ("${probeTarget}")。请运行 add_jhyy_to_user_path.ps1,或在设置里指定 jhyy.run.executorPath。`,
            '打开设置',
        );
        if (choice === '打开设置') {
            void vscode.commands.executeCommand('workbench.action.openSettings', 'jhyy.run.executorPath');
        }
        return;
    }

    if (!jhyyTerminal || jhyyTerminal.name !== terminalName) {
        const existing = vscode.window.terminals.find(t => t.name === terminalName);
        jhyyTerminal = existing ?? vscode.window.createTerminal(terminalName);
    }
    jhyyTerminal.show(true);

    const filePath = editor.document.uri.fsPath;
    const tmpl = mode === 'run'
        ? executor
        : executor.replace(/ run\b/, ' build');
    // JSON.stringify handles Windows backslashes + embedded quotes; required per
    // feedback_createproc_unquoted_tokenize (cmd.exe tokenizes on first whitespace).
    const cmd = tmpl.includes('{file}')
        ? tmpl.replace('{file}', JSON.stringify(filePath))
        : `${tmpl} ${JSON.stringify(filePath)}`;

    jhyyTerminal.sendText(cmd, true);
}

export function deactivate(): void {
    jhyyTerminal?.dispose();
}
