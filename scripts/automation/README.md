# Automation Scripts

This directory contains automation scripts for common PyNotebookLM workflows. These scripts demonstrate best practices for building production-ready automation on top of the library.

## Prerequisites

1. **Install PyNotebookLM:**
   ```bash
   pip install pynotebooklm
   ```

2. **Authenticate:**
   ```bash
   pynotebooklm auth login
   ```

3. **Install Rich (for nice console output):**
   ```bash
   pip install rich
   ```

## Scripts

### 1. `research_pipeline.py` - End-to-End Research Automation

Automates the complete research workflow from notebook creation to content generation.

**Features:**
- Creates a new notebook for a research topic
- Performs deep or standard web research
- Polls for research completion
- Automatically imports discovered sources
- Generates briefing documents
- Optionally creates audio/video overviews and study materials

**Usage:**
```bash
# Basic research pipeline
python scripts/automation/research_pipeline.py "Machine Learning"

# Deep research with audio overview
python scripts/automation/research_pipeline.py "Quantum Computing" --deep --audio

# Full pipeline with all content types
python scripts/automation/research_pipeline.py "Climate Change" --audio --video --study
```

**Options:**
- `--deep` - Use deep research mode (more comprehensive, takes longer)
- `--audio` - Generate audio overview after research
- `--video` - Generate video overview after research
- `--study` - Generate study materials (flashcards + quiz)
- `--max-polls N` - Maximum polling attempts (default: 24 = ~2 minutes)

**Example Output:**
```
Research Pipeline: Machine Learning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Creating notebook...
✅ Created notebook: Research: Machine Learning (nb_abc123)

Step 2: Starting deep research...
✅ Research session started: task_xyz789

Step 3: Waiting for research to complete...
✅ Research completed!

Discovered Sources
┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ # ┃ Title                        ┃ Type     ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 0 │ Introduction to ML - MIT     │ URL      │
│ 1 │ Neural Networks Explained    │ URL      │
└───┴──────────────────────────────┴──────────┘

Step 4: Importing 2 sources...
✅ Imported 2 sources successfully

Step 5: Creating briefing document...
✅ Briefing created: brief_123
```

---

### 2. `content_batch_generator.py` - Batch Content Generation

Generates content (audio, video, infographics, slides) for multiple notebooks concurrently.

**Features:**
- Processes multiple notebooks in parallel
- Configurable concurrency limits to avoid rate limits
- Progress tracking and error handling
- Support for all content types

**Usage:**
```bash
# Generate audio for specific notebooks
python scripts/automation/content_batch_generator.py \
  --type audio \
  --notebooks nb1,nb2,nb3

# Generate all content types from a file
python scripts/automation/content_batch_generator.py \
  --type all \
  --file notebooks.txt

# Custom concurrent limit
python scripts/automation/content_batch_generator.py \
  --type video \
  --file notebooks.txt \
  --concurrent 5
```

**Input File Format (notebooks.txt):**
```
nb_abc123
nb_def456
nb_ghi789
```

**Options:**
- `--type {audio,video,infographic,slides,all}` - Content type to generate
- `--notebooks ID1,ID2,...` - Comma-separated notebook IDs
- `--file PATH` - File containing notebook IDs (one per line)
- `--concurrent N` - Maximum concurrent operations (default: 3)

**Example Output:**
```
Batch Generation Results
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Notebook ID        ┃ Status   ┃ Details                    ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ nb_abc123          │ OK       │ audio: ✅ | video: ✅       │
│ nb_def456          │ OK       │ audio: ✅ | video: ✅       │
│ nb_ghi789          │ ERROR    │ No sources in notebook     │
└────────────────────┴──────────┴────────────────────────────┘

Summary: 2 successful, 1 errors
```

---

### 3. `backup_notebooks.py` - Export Notebooks to JSON

Exports all notebooks (with sources and artifacts) to JSON files for backup or migration.

**Features:**
- Exports notebook metadata, sources, and artifacts
- Supports individual or combined JSON files
- Timestamped exports
- Sanitized filenames

**Usage:**
```bash
# Backup to individual files (one per notebook)
python scripts/automation/backup_notebooks.py --output backups/

# Backup to a single combined file
python scripts/automation/backup_notebooks.py --single-file backup_2026-01-12.json

# Both individual and combined
python scripts/automation/backup_notebooks.py \
  --output backups/ \
  --single-file full_backup.json
```

**Options:**
- `--output DIR` - Directory for individual JSON files
- `--single-file PATH` - Single JSON file for all notebooks

**Export Format:**
```json
{
  "backup_date": "2026-01-12T10:30:00",
  "notebook_count": 5,
  "notebooks": [
    {
      "id": "nb_abc123",
      "name": "My Research",
      "created_at": "2026-01-10T14:20:00",
      "sources": [
        {
          "id": "src_xyz",
          "title": "Example Article",
          "type": "url",
          "url": "https://example.com"
        }
      ],
      "artifacts": [
        {
          "id": "art_123",
          "type": "audio",
          "status": "completed",
          "title": "Audio Overview"
        }
      ]
    }
  ]
}
```

---

### 4. `cleanup_old_artifacts.py` - Delete Old Artifacts

Bulk delete studio artifacts based on age, type, or status criteria.

**Features:**
- Filter by type (audio, video, etc.)
- Filter by status (completed, failed, in_progress)
- Filter by age (older than N days)
- Dry-run mode for safe testing
- Confirmation prompts

**Usage:**
```bash
# Dry run: Find artifacts older than 30 days
python scripts/automation/cleanup_old_artifacts.py --days 30 --dry-run

# Delete failed audio artifacts
python scripts/automation/cleanup_old_artifacts.py --type audio --status failed

# Clean specific notebook (with confirmation)
python scripts/automation/cleanup_old_artifacts.py --notebook-id nb_abc123

# Delete all completed artifacts over 60 days old (no confirmation)
python scripts/automation/cleanup_old_artifacts.py --days 60 --status completed --force
```

**Options:**
- `--notebook-id ID` - Specific notebook to clean (can specify multiple times)
- `--type TYPE` - Filter by artifact type
- `--status STATUS` - Filter by status (completed, failed, in_progress)
- `--days N` - Delete artifacts older than N days
- `--dry-run` - Preview without deleting
- `--force` - Skip confirmation prompt

**Example Output:**
```
Artifacts to Delete (15 total)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Artifact   ┃ Type       ┃ Status     ┃ Notebook           ┃ Created            ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ art_abc123 │ audio      │ failed     │ Research Project   │ 2025-12-01         │
│ art_def456 │ video      │ completed  │ Old Notes          │ 2025-11-15         │
└────────────┴────────────┴────────────┴────────────────────┴────────────────────┘

Delete 15 artifacts? [y/n]: y

Cleanup Complete!
Deleted: 14
Failed: 1
```

---

## Best Practices

### Rate Limiting

NotebookLM has rate limits. These scripts implement:
- **Batching**: Process items in small batches (default: 3 concurrent)
- **Automatic Retry**: Built-in exponential backoff via `RetryStrategy`
- **Progress Tracking**: Visual feedback for long-running operations

### Error Handling

All scripts follow these patterns:
1. **Graceful Degradation**: Continue processing other items if one fails
2. **Rich Error Messages**: Clear indication of what went wrong
3. **Exit Codes**: Non-zero on critical failures

### Environment Variables

Configure retry behavior:
```bash
export PYNOTEBOOKLM_MAX_RETRIES=5
export PYNOTEBOOKLM_BASE_DELAY=2.0
export PYNOTEBOOKLM_MAX_DELAY=60.0
```

Enable debug logging:
```bash
export PYNOTEBOOKLM_DEBUG=1
```

### Scheduling with Cron

Run scripts on a schedule (e.g., daily backups):

```bash
# Add to crontab (crontab -e)
# Daily backup at 3 AM
0 3 * * * /usr/bin/python3 /path/to/scripts/automation/backup_notebooks.py --single-file /backups/daily.json

# Weekly cleanup of failed artifacts (Sundays at 2 AM)
0 2 * * 0 /usr/bin/python3 /path/to/scripts/automation/cleanup_old_artifacts.py --status failed --force
```

## Customization

These scripts are designed to be customized for your specific needs. Key extension points:

1. **Custom Filters**: Add more sophisticated filtering logic
2. **Notification**: Integrate with email/Slack/Discord
3. **Report Generation**: Create HTML/PDF reports from backup data
4. **CI/CD Integration**: Run as part of automated workflows

## Troubleshooting

**Script hangs during research:**
- Research operations can take 60-120 seconds
- Increase `--max-polls` parameter
- Check network connectivity

**Rate limit errors:**
- Reduce `--concurrent` parameter
- Set `PYNOTEBOOKLM_MAX_RETRIES` higher
- Add delays between batches

**Authentication errors:**
- Run `pynotebooklm auth login` to refresh cookies
- Check `~/.pynotebooklm/auth.json` exists
- Cookies expire after ~2 weeks

## Contributing

Feel free to add more automation scripts! Follow the existing patterns:
1. Rich console output for visual appeal
2. Comprehensive error handling with try/except
3. Progress bars for long operations
4. Dry-run modes for destructive operations
5. Detailed docstrings and help text

## License

Apache 2.0 - Same as the main PyNotebookLM library.
