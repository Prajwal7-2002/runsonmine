# Add your machine to RunsOnMine

It takes about 5 minutes, most of it the model download. You need a computer with a local AI app
(Ollama is the easiest) and an internet connection. Nothing private is shared: only your hardware
model names, the model you tested, the speeds and whether the machine was plugged in.

**Before you start:** plug the laptop in, close games and video calls, and let it run without
using it for the 2-3 minutes the test takes.

## 1. Install Ollama and a model

Download Ollama from https://ollama.com/download (Mac, Windows or Linux) and open it. Then, in a
terminal (Mac: Terminal app; Windows: PowerShell):

```bash
ollama pull qwen2.5:0.5b
```

Have a bigger machine? Test more sizes; each one is a separate result:

| Your memory (GPU VRAM, or RAM on a Mac) | Also try |
| :--- | :--- |
| 6-8 GB | `qwen2.5:1.5b`, `qwen2.5:3b` |
| 12-16 GB | `qwen2.5:7b`, `mistral:7b` |
| 24 GB or more | `qwen2.5:14b`, `qwen2.5:32b` (if it fits) |

## 2. Install uv (runs servebench with the right Python, no setup)

**Mac or Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen the terminal afterwards.

## 3. Run the test

```bash
uvx servebench submit --model qwen2.5:0.5b
```

It finds Ollama by itself, runs the standard test (1, 2 and 4 users at once, about 2 minutes),
prints the whole result and saves it as `runsonmine-ollama-qwen2.5-0.5b.json` in the current folder.
Repeat with `--model qwen2.5:1.5b` and so on for each model you pulled.

Using llama.cpp or LM Studio instead? Start its server and run `uvx servebench submit` the same
way; it finds those too.

## 4. Send the result

Pick one:
- **GitHub:** open a pull request adding the file to
  [`data/results/`](https://github.com/Prajwal7-2002/runsonmine/tree/main/data/results). CI checks
  it automatically.
- **No GitHub account:** send the file to the maintainer (it is safe to share; open it in a text
  editor to see exactly what is in it).

A one-command upload is coming.

## Notes per platform

- **Mac (Apple Silicon):** the GPU shares the Mac's memory, so your RAM is the limit. GPU clock and
  power are not recorded on Macs; that is expected.
- **Windows laptops with NVIDIA:** check the result says `"power_source": "ac"`. If a laptop was on
  battery earlier, its GPU can stay power-capped even after plugging in; a restart fixes it.
- **Linux:** NVIDIA GPU clock and power are recorded if `nvidia-smi` works.
- **CPU only:** results are welcome too; they show what runs without a graphics card.

## Message you can send to friends

> Hey! I'm building RunsOnMine, a free site showing how fast AI models really run on real
> computers. Could you test yours? Takes 5 min:
> 1. Install Ollama (ollama.com), then run: `ollama pull qwen2.5:0.5b`
> 2. Install uv: Mac `curl -LsSf https://astral.sh/uv/install.sh | sh`, Windows
>    `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
> 3. Plugged in, run: `uvx servebench submit --model qwen2.5:0.5b`
> 4. Send me the `runsonmine-....json` file it creates.
>
> It only records hardware names and speeds, nothing personal. Thanks!
