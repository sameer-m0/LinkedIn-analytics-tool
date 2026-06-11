import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = r"c:\Users\samee\My Workspace\Linkedin Tool\LinkedIn-analytics-tool\backend\linkedin_analytics.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Get all real posts (excluding generated sample posts if any)
# Wait, let's look at all posts because the user might have mixed real and sample posts, or we want to study the real posts.
# Let's filter out 'Sample post #%' if we can, or just analyze all posts. Let's look at both options.
# Let's check posts where title does not start with 'Sample post #'
posts = [dict(r) for r in conn.execute("SELECT * FROM posts WHERE title NOT LIKE 'Sample post #%'").fetchall()]

if not posts:
    print("No real posts found, analyzing all posts.")
    posts = [dict(r) for r in conn.execute("SELECT * FROM posts").fetchall()]

print(f"Analyzing {len(posts)} posts...")

def has_emoji(text):
    if not text:
        return False
    # Simple heuristic for emojis/non-ascii or specific unicode ranges
    # Emojis are typically outside the BMP or in specific blocks
    # Let's check for characters with code points > 0x2000 that are not standard punctuation
    # Or just count non-ascii characters that are symbols
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50\u2b06\u2190-\u21ff\u2900-\u297f\u3030\u303d\u3297\u3299\U00002000-\U00003000]')
    return bool(emoji_pattern.search(text))

def count_hashtags(text):
    if not text:
        return 0
    return len(re.findall(r'#\w+', text))

def count_paragraphs(text):
    if not text:
        return 0
    # Split by newlines and count non-empty lines
    return len([p for p in text.split('\n') if p.strip()])

def has_link(text):
    if not text:
        return False
    return 'http' in text or 'lnkd.in' in text

def has_question(text):
    if not text:
        return False
    return '?' in text

def char_count(text):
    return len(text) if text else 0

def word_count(text):
    return len(text.split()) if text else 0

# Enrich posts with features
for p in posts:
    p['char_len'] = char_count(p['title'])
    p['word_len'] = word_count(p['title'])
    p['hashtags'] = count_hashtags(p['title'])
    p['paragraphs'] = count_paragraphs(p['title'])
    p['has_emoji'] = has_emoji(p['title'])
    p['has_link'] = has_link(p['title'])
    p['has_question'] = has_question(p['title'])
    p['er'] = p['engagement_rate'] or 0.0
    p['imp'] = p['impressions'] or 0

# Sort posts by engagement rate and impressions to define high performers
posts_by_er = sorted(posts, key=lambda x: x['er'], reverse=True)
posts_by_imp = sorted(posts, key=lambda x: x['imp'], reverse=True)

top_er_threshold = posts_by_er[max(0, len(posts)//4)]['er']
top_imp_threshold = posts_by_imp[max(0, len(posts)//4)]['imp']

print(f"Top 25% Engagement Rate Threshold: {top_er_threshold*100:.2f}%")
print(f"Top 25% Impressions Threshold: {top_imp_threshold:,} impressions")

def analyze_group(group_posts, label):
    n = len(group_posts)
    if n == 0:
        return
    avg_er = sum(p['er'] for p in group_posts) / n
    avg_imp = sum(p['imp'] for p in group_posts) / n
    avg_len = sum(p['char_len'] for p in group_posts) / n
    avg_words = sum(p['word_len'] for p in group_posts) / n
    avg_hash = sum(p['hashtags'] for p in group_posts) / n
    pct_emoji = sum(1 for p in group_posts if p['has_emoji']) / n
    pct_link = sum(1 for p in group_posts if p['has_link']) / n
    pct_question = sum(1 for p in group_posts if p['has_question']) / n
    avg_para = sum(p['paragraphs'] for p in group_posts) / n
    
    print(f"\nGroup: {label} (N={n})")
    print(f"  Avg Engagement Rate: {avg_er*100:.2f}%")
    print(f"  Avg Impressions:     {avg_imp:,.0f}")
    print(f"  Avg Char Length:     {avg_len:.1f}")
    print(f"  Avg Word Length:     {avg_words:.1f}")
    print(f"  Avg Hashtags:        {avg_hash:.1f}")
    print(f"  Avg Paragraphs:      {avg_para:.1f}")
    print(f"  Has Emoji %:         {pct_emoji*100:.1f}%")
    print(f"  Has Link %:          {pct_link*100:.1f}%")
    print(f"  Has Question %:      {pct_question*100:.1f}%")

# 1. Compare High Engagement posts vs Rest
high_er_posts = [p for p in posts if p['er'] >= top_er_threshold]
low_er_posts = [p for p in posts if p['er'] < top_er_threshold]
analyze_group(high_er_posts, "High Engagement (Top 25%)")
analyze_group(low_er_posts, "Lower Engagement (Bottom 75%)")

# 2. Compare High Reach posts vs Rest
high_imp_posts = [p for p in posts if p['imp'] >= top_imp_threshold]
low_imp_posts = [p for p in posts if p['imp'] < top_imp_threshold]
analyze_group(high_imp_posts, "High Reach (Top 25%)")
analyze_group(low_imp_posts, "Lower Reach (Bottom 75%)")

conn.close()
