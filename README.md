# YouTube Monitor & Translator

> **AI-Powered Automatic YouTube Video Monitoring and Translation System**

[中文版](README_zh.md)

Automatically monitors YouTube channels, downloads English subtitles, and generates high-quality Chinese translations and structured summaries using Claude AI.

## Features

- **Auto Monitoring** - RSS subscription monitoring for 16+ high-quality tech/business channels
- **Smart Subtitle Processing** - SRT parsing + intelligent merging (by time interval and sentence boundaries)
- **AI Analysis** - Auto-generates summaries, chapters, and speaker identification
- **High-Quality Translation** - Segmented translation + context maintenance + terminology consistency
- **Fine-Grained Timestamps** - ~1 minute granularity for quick content location
- **Content Review** - Chapter restructuring + AI garbage cleanup
- **Email Notifications** - Automatic email upon completion

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Ensure Claude CLI is Available

```bash
claude --version
```

### 3. Process a Single Video

```bash
python main.py --video VIDEO_ID
```

### 4. Monitor All Channels

```bash
# Single run
python main.py

# Continuous loop (check every N hours)
python main.py --loop
```

## Project Architecture

```
youtube-monitor-translator/
├── core/                    # Core business logic
│   ├── video_discovery.py   # Stage 1: RSS monitoring
│   ├── content_fetcher.py   # Stage 2: Subtitle download
│   ├── subtitle_processor.py # Stage 3: Subtitle processing
│   ├── ai_analyzer.py       # Stage 4: AI analysis
│   ├── chapter_optimizer.py # Stage 5: Chapter optimization
│   ├── translator.py        # Stage 6: Translation engine
│   ├── reviewer.py          # Stage 6.5: Content review
│   ├── output_generator.py  # Stage 7: Output generation
│   └── pipeline.py          # Pipeline coordinator
├── infrastructure/          # Infrastructure layer
│   ├── config.py            # Configuration management
│   ├── logger.py            # Logging system
│   ├── archive.py           # Archive management
│   └── notifier.py          # Email notifications
├── utils/                   # Utility functions
├── prompts/                 # AI Prompt templates
├── tests/                   # Test suite
├── ai_output/               # Output directory
│   ├── srt/                 # Raw subtitles
│   ├── clean/               # Processed subtitles
│   └── summary/             # Final translations
├── config_ai.json           # System configuration
└── channels.json            # Channel list
```

## Processing Pipeline

```
RSS Monitor → Video Filter → Subtitle Download → Subtitle Process → AI Analysis
    ↓
Chapter Optimize → Segment Translate → Content Review → Output Generate → Email Notify
```

| Stage | Function | Technology |
|-------|----------|------------|
| 1. Video Discovery | RSS monitoring + duration filter | feedparser |
| 2. Content Fetch | Subtitle download + metadata | yt-dlp |
| 3. Subtitle Process | SRT parsing + smart merge | Custom algorithm |
| 4. AI Analysis | Summary + chapters + speakers | Claude CLI |
| 5. Chapter Optimize | Merge short / split long | Smart algorithm |
| 6. Segment Translate | Context maintenance + retry | Claude CLI |
| 6.5. Content Review | Chapter restructure + AI cleanup | Python + haiku |
| 7. Output Generate | Markdown generation | Template engine |

## Configuration

Edit `config_ai.json`:

```json
{
  "claude_model": "claude-sonnet-4-20250514",
  "claude_timeout_seconds": 600,
  "min_duration_minutes": 10,
  "min_chapter_duration": 180,
  "max_chapter_duration": 900,
  "context_lines": 5,
  "review_enabled": true,
  "review_remove_ai_garbage": true,
  "email_enabled": false,
  "check_interval_hours": 5
}
```

### Model Options

| Model | Use Case | Notes |
|-------|----------|-------|
| `claude-opus-4-20250514` | Best quality | Most expensive |
| `claude-sonnet-4-20250514` | Recommended | Balance of quality and cost |
| `claude-3-5-haiku-latest` | Fast | Used for review module |

## Output Example

Generated Markdown includes:

```markdown
# Video Title

## Video Info
- Channel: xxx
- Published: 2025-01-01
- Duration: 45:30

## TL;DR
One-sentence summary...

## Chapter Navigation
| Timestamp | Chapter Title | Summary |
|-----------|---------------|---------|
| 00:00-05:30 | Introduction | ... |

## Full Translation

### (0:00 - 5:30) Introduction
> Chapter summary

**(0:00 - 1:15)**
Translation content...

**(1:15 - 2:30)**
Translation content...
```

## Monitored Channels

Default monitored channels (configurable in `channels.json`):

- a16z
- All-In Podcast
- Lex Fridman
- Dwarkesh Patel
- No Priors
- 20VC with Harry Stebbings
- Machine Learning Street Talk
- And more...

## Email Notifications

1. Copy the configuration template:
```bash
cp .env.example .env
```

2. Edit `.env` or create `email_config.py`:
```python
EMAIL_SENDER = "your-email@gmail.com"
EMAIL_RECEIVER = "recipient@gmail.com"
EMAIL_PASSWORD = "your-app-password"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
MAIL_ENABLE = True
```

3. Enable in `config_ai.json`:
```json
{
  "email_enabled": true
}
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific tests
pytest tests/test_pipeline.py -v
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Complete development blueprint (AI guide)
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - System architecture design
- [FINAL_STATUS.md](FINAL_STATUS.md) - Project status report

## Tech Stack

- **Python 3.11+**
- **Claude CLI** - AI analysis and translation
- **yt-dlp** - Video/subtitle download
- **feedparser** - RSS parsing
- **pytest** - Unit testing

## License

MIT

---

**v2.0.0** - Complete refactoring, modular architecture, professional code standards
