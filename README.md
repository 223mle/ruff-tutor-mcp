# Ruff Tutor MCP

**Ruff violations as learning opportunities, not just auto-fixes**

[日本語](#日本語) | [English](#english)

---

## English

### Overview

Ruff Tutor MCP is an MCP (Model Context Protocol) server that detects Ruff violations in Python code and teaches you **why the code is problematic**, rather than just fixing it automatically.

### The Problem with Traditional Workflows

```
1. Detect code violations with Ruff
2. Claude Code auto-fixes them
3. Done!
```

**Issue**: Convenient, but you lose the opportunity to learn proper coding practices.

### Ruff Tutor's Approach

```
1. Detect code violations with Ruff
2. Explain why the code is problematic
3. Present relevant PEPs and best practices
4. Show correct code examples
5. Fix after the user understands
```

**Result**: Maintain convenience while creating learning opportunities.

### Features

#### 1. `review_code_and_teach`

Check code and generate learning materials.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | `"."` | Path to check |
| `mode` | `str \| None` | `None` | Learning mode (beginner, advanced, auto) |

**Learning Modes:**

- **beginner**: Shows Before/After examples with detailed explanations, prompts user to fix
- **advanced**: No Before/After shown, only explanations to make the user think
- **auto**: Shows explanations then auto-fixes

#### 2. `verify_fix`

Verify user's fix and show Before/After if violations remain.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | `"."` | Path to check |
| `previous_codes` | `list[str] \| None` | `None` | List of previously detected violation codes |
| `retry_count` | `int` | `0` | Retry count |

### Installation

#### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Ruff](https://docs.astral.sh/ruff/) linter

#### Install Package

```bash
# Install with uv
uv pip install ruff-tutor-mcp

# Or install in development mode
git clone https://github.com/yourusername/ruff-tutor-mcp.git
cd ruff-tutor-mcp
uv sync
```

### MCP Server Configuration

#### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "ruff-tutor": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/ruff-tutor-mcp",
        "ruff-tutor-mcp"
      ]
    }
  }
}
```

#### Claude Code

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "ruff-tutor": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/ruff-tutor-mcp",
        "ruff-tutor-mcp"
      ]
    }
  }
}
```

#### Using uvx (Recommended)

If the package is published to PyPI:

```json
{
  "mcpServers": {
    "ruff-tutor": {
      "command": "uvx",
      "args": ["ruff-tutor-mcp"]
    }
  }
}
```

### Configuration File

Place `.ruff-tutor.toml` in your project root to customize default behavior:

```toml
# .ruff-tutor.toml

# Learning mode: "beginner", "advanced", "auto"
mode = "beginner"

# Maximum retry count in advanced mode (1-10)
max_retry = 2
```

#### Configuration Priority

1. `mode` parameter in tool call
2. `.ruff-tutor.toml` file
3. Default values (beginner mode)

### Usage Example

Ask Claude:

```
Review this project's code and teach me if there are any issues
```

Claude will call `review_code_and_teach` and display results like:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[F401] unused-import  (src/example.py:3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before | After
-------|-------
import os, sys | import sys

🔍 Why is this a problem?
Unused imports reduce code readability and confuse other developers
wondering "Is this module being used?"...

📚 Background & Best Practices
PEP 8 recommends removing unused imports...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 日本語

### 概要

Ruff Tutor MCP は、Python コードの Ruff 違反を検出し、単に修正するだけでなく、**なぜそのコードが問題なのか**を教えてくれる MCP (Model Context Protocol) サーバーです。

### 従来のワークフローの課題

```
1. Ruff でコード違反を検知
2. Claude Code などのツールが自動修正
3. 完了！
```

**問題点**: 便利だが、正しいコードの書き方やルールを学ぶ機会が失われる

### Ruff Tutor のアプローチ

```
1. Ruff でコード違反を検知
2. なぜそのコードが問題なのかを説明
3. 関連する PEP やベストプラクティスを提示
4. 正しいコード例を示す
5. ユーザーが理解してから修正
```

**結果**: 便利さを保ちながら、学習機会を創出

### 機能

#### 1. `review_code_and_teach`

コードをチェックし、学習教材を生成します。

**パラメータ:**
| パラメータ | 型 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `path` | `str` | `"."` | チェック対象のパス |
| `mode` | `str \| None` | `None` | 学習モード（beginner, advanced, auto） |

**学習モード:**

- **beginner**: Before/After の例を表示し、詳しい説明付きでユーザーに修正を促す
- **advanced**: Before/After を表示せず、説明のみでユーザーに考えさせる
- **auto**: 説明を表示した後、自動修正を実行

#### 2. `verify_fix`

ユーザーの修正を検証し、まだ違反が残っている場合は Before/After を表示します。

**パラメータ:**
| パラメータ | 型 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `path` | `str` | `"."` | チェック対象のパス |
| `previous_codes` | `list[str] \| None` | `None` | 以前検出された違反コードのリスト |
| `retry_count` | `int` | `0` | リトライ回数 |

### インストール

#### 前提条件

- Python 3.11 以上
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー
- [Ruff](https://docs.astral.sh/ruff/) リンター

#### パッケージのインストール

```bash
# uv でインストール
uv pip install ruff-tutor-mcp

# または開発モードでインストール
git clone https://github.com/yourusername/ruff-tutor-mcp.git
cd ruff-tutor-mcp
uv sync
```

### MCP サーバーの設定

#### Claude Desktop での設定

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) または `%APPDATA%\Claude\claude_desktop_config.json` (Windows) に以下を追加:

```json
{
  "mcpServers": {
    "ruff-tutor": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/ruff-tutor-mcp",
        "ruff-tutor-mcp"
      ]
    }
  }
}
```

#### Claude Code での設定

`.claude/settings.json` に以下を追加:

```json
{
  "mcpServers": {
    "ruff-tutor": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/ruff-tutor-mcp",
        "ruff-tutor-mcp"
      ]
    }
  }
}
```

#### uvx を使った設定（推奨）

パッケージが PyPI に公開されている場合:

```json
{
  "mcpServers": {
    "ruff-tutor": {
      "command": "uvx",
      "args": ["ruff-tutor-mcp"]
    }
  }
}
```

### 設定ファイル

プロジェクトルートに `.ruff-tutor.toml` を配置することで、デフォルトの動作をカスタマイズできます。

```toml
# .ruff-tutor.toml

# 学習モード: "beginner", "advanced", "auto"
mode = "beginner"

# advanced モードでの最大リトライ回数 (1-10)
max_retry = 2
```

#### 設定の優先順位

1. ツール呼び出し時の `mode` パラメータ
2. `.ruff-tutor.toml` ファイル
3. デフォルト値（beginner モード）

### 使用例

Claude に以下のように依頼します:

```
このプロジェクトのコードをレビューして、問題があれば教えてください
```

Claude は `review_code_and_teach` ツールを呼び出し、以下のような形式で結果を表示します:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[F401] unused-import  (src/example.py:3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before | After
-------|-------
import os, sys | import sys

🔍 Why is this a problem?
未使用のインポートはコードの可読性を低下させ、
他の開発者が「このモジュールは使われているのか？」と
混乱する原因になります...

📚 Background & Best Practices
PEP 8 では、使用しないインポートを削除することを推奨しています...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Architecture

```
src/ruff_tutor_mcp/
├── main.py              # MCP entry point (tool definitions)
├── config.py            # Configuration management (TOML loading)
│
├── models/              # Domain model layer
│   ├── violation.py     # RuffViolation - violation info
│   ├── rule.py          # RuffRule - rule explanation
│   ├── fix.py           # CodeFix - fix info
│   └── result.py        # RuffAnalyzeResult - analysis result
│
├── services/            # Business logic layer
│   ├── analyzer.py      # RuffAnalyzer - analysis orchestration
│   ├── diffparser.py    # DiffParser - unified diff parsing
│   └── tutor.py         # TutorService - response generation
│
├── commands/            # External command execution layer
│   └── ruff.py          # RuffCommand - ruff command wrapper
│
└── templates/           # Instruction templates
    └── instructions.py  # Instructions for each mode
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/ruff-tutor-mcp.git
cd ruff-tutor-mcp
uv sync --group dev
```

### Run Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_analyzer.py
```

### Linter and Formatter

```bash
# Lint check
uv run ruff check src/ tests/

# Format check
uv run ruff format --check src/ tests/

# Auto format
uv run ruff format src/ tests/
```

### Type Check

```bash
uv run mypy src/ tests/
```

### All Quality Checks (tox)

```bash
uv run tox
```

## License

MIT License

## Contributing

Issues and Pull Requests are welcome.
