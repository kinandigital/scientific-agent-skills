# Development

Source: https://pi.dev/docs/latest/development

Use this when working on Pi itself.

## Setup

```bash
git clone https://github.com/earendil-works/pi-mono
cd pi-mono
bun install
bun run build
```

Run from source:

```bash
/path/to/pi-mono/pi-test.sh
```

The script can be run from any directory and preserves the caller's cwd.

## Forking and Rebranding

Configure `package.json`:

```json
{
  "piConfig": {
    "name": "pi",
    "configDir": ".pi"
  }
}
```

Change `name`, `configDir`, and `bin` for a fork. This affects CLI banner, config paths, and environment variable names.

## Path Resolution

Pi has bun install, standalone binary, and tsx-from-source execution modes. Always use `src/config.ts` helpers such as `getPackageDir` and `getThemeDir` for package assets. Do not use `__dirname` directly for assets.

## Debugging and Tests

`/debug` writes rendered TUI lines and last LLM messages to `~/.pi/agent/pi-debug.log`.

```bash
./test.sh
bun test
bun test -- test/specific.test.ts
```

## Project Structure

```text
packages/
  ai/            # LLM provider abstraction
  agent/         # Agent loop and message types
  tui/           # Terminal UI components
  coding-agent/  # CLI and interactive mode
```
