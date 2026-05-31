"""
Book Writer Skill — sequential chapter summarization and Book Bible builder.
Lets the AI work with full novels that exceed context size by maintaining
structured summaries of each chapter in a book-bible.md file.
"""


def execute(**kwargs):
    import json
    from pathlib import Path

    action         = kwargs.get('action', 'list_chapters')
    book_json_path = kwargs.get('book_json_path', '')
    chapter_index  = kwargs.get('chapter_index', -1)
    output_path    = kwargs.get('output_path', '')

    # ── Locate book.json ────────────────────────────────────────────
    if not book_json_path:
        # Auto-search common locations
        candidates = [
            Path.cwd() / 'workspace' / 'book.json',
        ]
        # Walk all subdirs of cwd up to 3 levels for book.json
        for p in Path.cwd().rglob('book.json'):
            candidates.append(p)
        for c in candidates:
            if c.exists():
                book_json_path = str(c)
                break

    if not book_json_path:
        return 'ERROR: No book.json found. Pass book_json_path or place book.json in workspace.'

    book_path = Path(book_json_path)
    if not book_path.exists():
        return f'ERROR: book.json not found at {book_json_path}'

    try:
        book = json.loads(book_path.read_text(encoding='utf-8', errors='replace'))
    except Exception as e:
        return f'ERROR reading book.json: {e}'

    chapters = book.get('chapters', [])
    book_dir = book_path.parent
    bible_path = Path(output_path) if output_path else book_dir / 'book-bible.md'

    # ── Actions ─────────────────────────────────────────────────────

    if action == 'list_chapters':
        lines = [f'# {book.get("title", "Untitled")} — Chapter List\n']
        for i, ch in enumerate(chapters):
            fp = Path(ch.get('filePath', ''))
            exists = '✓' if fp.exists() else '✗ (missing)'
            wc = ''
            if fp.exists():
                try:
                    words = len(fp.read_text(encoding='utf-8', errors='replace').split())
                    wc = f' ({words:,} words)'
                except Exception:
                    pass
            lines.append(f'{i}. Chapter {ch.get("number", i+1)}: {ch.get("title", "?")} {exists}{wc}')
        lines.append(f'\nTotal chapters: {len(chapters)}')
        lines.append(f'Book bible: {"EXISTS" if bible_path.exists() else "not yet built"} → {bible_path}')
        return '\n'.join(lines)

    if action == 'summarize_chapter':
        idx = int(chapter_index)
        if idx < 0 or idx >= len(chapters):
            return f'ERROR: chapter_index {idx} out of range (0–{len(chapters)-1})'
        ch = chapters[idx]
        fp = Path(ch.get('filePath', ''))
        if not fp.exists():
            return f'ERROR: Chapter file not found: {fp}'
        text = fp.read_text(encoding='utf-8', errors='replace')
        word_count = len(text.split())
        # Return the raw chapter text so the LLM can summarize it
        # The agent loop will call this, get the text, then produce a summary
        return (
            f'=== CHAPTER {ch.get("number", idx+1)}: {ch.get("title", "?")} ===\n'
            f'Word count: {word_count:,}\n'
            f'File: {fp}\n\n'
            f'{text[:12000]}'  # cap at ~3K tokens to fit in context
            + (f'\n\n[...truncated, {word_count - len(text[:12000].split())} words remaining...]'
               if word_count > 3000 else '')
        )

    if action == 'save_bible':
        content = kwargs.get('content', '')
        if not content:
            return 'ERROR: No content provided. Pass the full book-bible.md text as content.'
        bible_path.parent.mkdir(parents=True, exist_ok=True)
        bible_path.write_text(content, encoding='utf-8')
        return f'Book Bible saved to {bible_path} ({len(content):,} chars, ~{len(content)//4:,} tokens)'

    if action == 'get_context':
        if not bible_path.exists():
            return 'ERROR: Book Bible not found. Run /bookcontext first to build it.'
        bible = bible_path.read_text(encoding='utf-8', errors='replace')
        # Optionally append the last chapter for style continuity
        last_chapter_text = ''
        if chapters:
            last_fp = Path(chapters[-1].get('filePath', ''))
            if last_fp.exists():
                try:
                    last_text = last_fp.read_text(encoding='utf-8', errors='replace')
                    last_chapter_text = (
                        f'\n\n---\n## LAST CHAPTER (for style reference)\n\n'
                        f'{last_text[:6000]}'
                    )
                except Exception:
                    pass
        return (
            f'=== BOOK BIBLE ===\n\n{bible}'
            f'{last_chapter_text}\n\n'
            f'=== END BOOK CONTEXT ===\n'
            f'Total: ~{(len(bible) + len(last_chapter_text)) // 4:,} tokens'
        )

    if action == 'build_bible':
        # Return instructions for the agent to follow — it will call summarize_chapter
        # for each chapter one by one, then call save_bible with the assembled result
        chapter_list = '\n'.join(
            f'  - Index {i}: Chapter {ch.get("number", i+1)} — {ch.get("title", "?")}'
            for i, ch in enumerate(chapters)
        )
        return (
            f'Book: {book.get("title", "Untitled")} ({len(chapters)} chapters)\n'
            f'To build the Book Bible, call summarize_chapter for each index below,\n'
            f'then assemble all summaries plus master character/timeline sheets,\n'
            f'then call save_bible with the complete markdown content.\n\n'
            f'Chapter indices to process:\n{chapter_list}\n\n'
            f'Output file: {bible_path}'
        )

    return f'ERROR: Unknown action "{action}". Valid: list_chapters, summarize_chapter, build_bible, get_context, save_bible'
