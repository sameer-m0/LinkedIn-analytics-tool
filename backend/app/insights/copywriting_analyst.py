import re
from datetime import datetime
from app.models.post import Post
from app.insights import text_utils as T

def analyze_post_copywriting(
    p: Post, 
    median_impressions: float, 
    avg_engagement: float
) -> dict:
    body = p.title or ""
    
    # 1. Extract Hook (first 1-2 lines before double linebreak or first 150 chars)
    hook_text = ""
    paragraphs = [pg.strip() for pg in body.split("\n") if pg.strip()]
    if paragraphs:
        hook_text = paragraphs[0]
        if len(hook_text) < 60 and len(paragraphs) > 1:
            hook_text += " " + paragraphs[1]
    if not hook_text:
        hook_text = body[:150].strip()
        
    # Hook effectiveness rating
    hook_lower = hook_text.lower()
    has_question = "?" in hook_text
    has_numbers = any(char.isdigit() for char in hook_text)
    has_triggers = any(word in hook_lower for word in ["secret", "why", "how to", "stop", "never", "how i", "framework", "tips", "announcing"])
    
    if T.has_link(hook_text):
        hook_effectiveness = "Low"
    elif (has_question or has_numbers or has_triggers) and len(hook_text) > 30:
        hook_effectiveness = "High"
    elif len(hook_text) < 25:
        hook_effectiveness = "Low"
    else:
        hook_effectiveness = "Medium"

    # 2. Tone Detection
    tone_keywords = {
        "Storytelling": ["i ", "my ", "ago", "working with", "journey", "learned", "fail", "build", "year", "career", "team", "decided", "started"],
        "Educational": ["how to", "tips", "framework", "tutorial", "guide", "steps", "lessons", "here is", "resource", "learn"],
        "Promotional": ["hiring", "job", "join", "apply", "excited", "launch", "product", "demo", "sign up", "we are", "event"],
        "Conversational": ["agree?", "thoughts?", "what do you think?", "let me know", "comment below", "how do you"],
        "Technical": ["code", "architecture", "database", "api", "system", "git", "deploy", "rust", "python", "javascript", "react", "postgres", "sql"]
    }
    
    body_lower = body.lower()
    tone_scores = {t: 0 for t in tone_keywords}
    for tone, keywords in tone_keywords.items():
        for kw in keywords:
            tone_scores[tone] += body_lower.count(kw)
            
    max_tone = max(tone_scores, key=tone_scores.get)
    if tone_scores[max_tone] == 0:
        detected_tone = "Insightful"
    else:
        detected_tone = max_tone
        
    tone_explanations = {
        "Storytelling": "Uses a narrative approach to share experiences, which builds personal connection and emotional resonance.",
        "Educational": "Delivers direct value through actionable guides, frameworks, or advice to position you as an expert.",
        "Promotional": "Aimed at sharing exciting team launches, career openings, or company events to drive action.",
        "Conversational": "Invites high engagement and comment section activity by directly asking readers for their input.",
        "Technical": "Shares developer-centric concepts or architectural decisions to build credibility in engineering networks.",
        "Insightful": "Presents structured business or professional takeaways in a concise, authoritative manner."
    }
    tone_explanation = tone_explanations.get(detected_tone, "Provides clean, structured professional insights.")

    # 3. Key Hooks (rhetorical questions, list highlights, bold claims)
    key_hooks = []
    # Rhetorical questions
    for line in body.split("\n"):
        line_clean = line.strip()
        if "?" in line_clean and len(line_clean) > 20 and len(key_hooks) < 2:
            key_hooks.append(line_clean)
            
    # Bold starting points or list items
    list_item_rx = re.compile(r"^\s*[-*•\d+.]\s*(.*)")
    for line in body.split("\n"):
        line_clean = line.strip()
        match = list_item_rx.match(line_clean)
        if match and len(line_clean) > 25 and len(key_hooks) < 3:
            content = match.group(1).strip()
            if content and content not in key_hooks:
                key_hooks.append(line_clean)
                
    # Fallback to first line if empty
    if not key_hooks and paragraphs:
        key_hooks.append(paragraphs[0])

    # 4. Convincing Elements
    convincing_elements = []
    if len(paragraphs) > 4:
        convincing_elements.append("Excellent formatting: Short, scannable paragraphs encourage reading on mobile screens.")
    if has_question:
        convincing_elements.append("Direct question in hook engages immediate curiosity.")
    if T.extract_tagged_people(body):
        convincing_elements.append("Tagging collaborators extends post reach directly into their professional network.")
    if any(char.isdigit() for char in body):
        convincing_elements.append("Includes concrete numbers or metrics to back up claims.")
    if p.impressions > median_impressions and median_impressions > 0:
        mult = p.impressions / median_impressions
        convincing_elements.append(f"High impressions ({mult:.1f}x median): Topic is highly resonant with your audience.")
    if p.engagement_rate is not None and p.engagement_rate > avg_engagement and avg_engagement > 0:
        convincing_elements.append(f"Strong {p.engagement_rate*100:.1f}% engagement: Persuasive copy motivated interactions.")
    if not convincing_elements:
        convincing_elements.append("Clean structure with a focused theme that keeps the reader's attention.")

    # 5. Improvement Suggestions
    improvement_suggestions = []
    # Wall of text check (average characters per paragraph)
    non_empty_p = [p for p in paragraphs if len(p) > 20]
    if len(non_empty_p) > 0:
        avg_p_len = sum(len(p) for p in non_empty_p) / len(non_empty_p)
        if avg_p_len > 350:
            improvement_suggestions.append("Break down longer paragraphs (over 3-4 lines) to avoid a 'wall of text' that causes mobile readers to scroll past.")
            
    if T.has_link(body):
        improvement_suggestions.append("Move external link to the comments section to prevent LinkedIn's algorithm from suppressing post reach.")
        
    if not any("?" in line for line in body.split("\n")[-2:]):
        improvement_suggestions.append("End with a clear, open-ended question to spark conversations and boost engagement in the comments.")
        
    hashtags = T.extract_hashtags(body)
    if not hashtags:
        improvement_suggestions.append("Add 3-5 relevant hashtags at the bottom to increase discoverability in LinkedIn topic search feeds.")
    elif len(hashtags) > 8:
        improvement_suggestions.append("Reduce the number of hashtags (currently too high) to make the post look less spammy and focus reach.")
        
    if p.engagement_rate is not None and p.engagement_rate < avg_engagement and avg_engagement > 0:
        improvement_suggestions.append("The hook may be too weak; try starting with a bold contrarian statement or a key lesson learned.")
        
    if not improvement_suggestions:
        improvement_suggestions.append("Formatting is solid. Try testing a different format (like carousel/image) to push engagement further.")

    return {
        "hook": hook_text,
        "hook_effectiveness": hook_effectiveness,
        "tone": detected_tone,
        "tone_explanation": tone_explanation,
        "key_hooks": key_hooks[:3],
        "convincing_elements": convincing_elements[:3],
        "improvement_suggestions": improvement_suggestions[:3]
    }
