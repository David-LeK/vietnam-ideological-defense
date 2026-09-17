import re
import json
import os

def parse_markdown_file(filepath, lang):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by H1 headers like # 1. Title or # 88. Title
    topic_blocks = re.split(r'\n(?=# \d+\.\s+)', content)
    
    topics = []
    
    for block in topic_blocks:
        block = block.strip()
        if not block.startswith('# '):
            continue
        
        lines = block.split('\n')
        header_line = lines[0].strip()
        
        header_match = re.match(r'# (\d+)\.\s+(.*)', header_line)
        if not header_match:
            continue
            
        topic_id = int(header_match.group(1))
        topic_title = header_match.group(2).strip()
        
        allegation_pattern = r'\*\*(?:Allegation|Luận điệu):\*\*\s*(.*?)(?=\n\*\*(?:Allegation|Luận điệu):\*\*|$)'
        allegation_matches = list(re.finditer(allegation_pattern, block, re.DOTALL))
        
        allegations = []
        for idx, match in enumerate(allegation_matches):
            raw_text = match.group(1).strip()
            text_lines = raw_text.split('\n')
            
            allegation_text = ""
            refutations = []
            facts = []
            
            for l in text_lines:
                l_str = l.strip()
                if not l_str:
                    continue
                if not allegation_text and not l_str.startswith('*'):
                    allegation_text = l_str
                elif l_str.startswith('*'):
                    clean_bullet = re.sub(r'^\*\s*', '', l_str).strip()
                    refutations.append(clean_bullet)
                    if 'Fact:' in clean_bullet or 'Historical Context:' in clean_bullet or 'Số liệu:' in clean_bullet or 'Bối cảnh lịch sử:' in clean_bullet or 'Theo ' in clean_bullet or 'Oxfam' in clean_bullet or 'World Bank' in clean_bullet:
                        facts.append(clean_bullet)
            
            allegations.append({
                "id": f"{topic_id}.{idx + 1}",
                "topicId": topic_id,
                "topicTitle": topic_title,
                "allegation": allegation_text,
                "refutations": refutations,
                "facts": facts
            })
            
        topics.append({
            "id": topic_id,
            "title": topic_title,
            "allegationCount": len(allegations),
            "allegations": allegations
        })
        
    return topics

def combine_en_vi(en_topics, vi_topics):
    en_dict = {t['id']: t for t in en_topics}
    vi_dict = {t['id']: t for t in vi_topics}
    
    all_topic_ids = sorted(list(set(list(en_dict.keys()) + list(vi_dict.keys()))))
    
    combined_topics = []
    total_allegations = 0
    total_facts = 0
    total_refutations = 0
    
    for tid in all_topic_ids:
        en_t = en_dict.get(tid, {})
        vi_t = vi_dict.get(tid, {})
        
        title_en = en_t.get('title', vi_t.get('title', ''))
        title_vi = vi_t.get('title', en_t.get('title', ''))
        
        en_algs = en_t.get('allegations', [])
        vi_algs = vi_t.get('allegations', [])
        
        max_len = max(len(en_algs), len(vi_algs))
        combined_algs = []
        
        for i in range(max_len):
            en_a = en_algs[i] if i < len(en_algs) else {}
            vi_a = vi_algs[i] if i < len(vi_algs) else {}
            
            alg_id = f"{tid}.{i + 1}"
            
            facts_en = en_a.get('facts', [])
            facts_vi = vi_a.get('facts', [])
            
            ref_en = en_a.get('refutations', [])
            ref_vi = vi_a.get('refutations', [])
            
            total_refutations += max(len(ref_en), len(ref_vi))
            
            if facts_en or facts_vi:
                total_facts += 1
                
            total_allegations += 1
            
            combined_algs.append({
                "id": alg_id,
                "topicId": tid,
                "title_en": title_en,
                "title_vi": title_vi,
                "allegation_en": en_a.get('allegation', ''),
                "allegation_vi": vi_a.get('allegation', ''),
                "refutations_en": ref_en,
                "refutations_vi": ref_vi,
                "facts_en": facts_en,
                "facts_vi": facts_vi,
                "hasFact": len(facts_en) > 0 or len(facts_vi) > 0
            })
            
        combined_topics.append({
            "id": tid,
            "title_en": title_en,
            "title_vi": title_vi,
            "allegationCount": max_len,
            "allegations": combined_algs
        })
        
    stats = {
        "totalTopics": len(combined_topics),
        "totalAllegations": total_allegations,
        "totalRefutations": total_refutations,
        "totalFacts": total_facts
    }
    
    return {
        "stats": stats,
        "topics": combined_topics
    }

if __name__ == '__main__':
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    en_file = os.path.join(root_dir, 'core_arguments_en.md')
    vi_file = os.path.join(root_dir, 'core_arguments_vi.md')
    
    print(f"Parsing {en_file}...")
    en_topics = parse_markdown_file(en_file, 'en')
    print(f"Parsed {len(en_topics)} EN topics.")
    
    print(f"Parsing {vi_file}...")
    vi_topics = parse_markdown_file(vi_file, 'vi')
    print(f"Parsed {len(vi_topics)} VI topics.")
    
    bundle = combine_en_vi(en_topics, vi_topics)
    
    json_path = os.path.join(root_dir, 'arguments_bundle.json')
    js_path = os.path.join(root_dir, 'arguments_bundle.js')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON bundle to {json_path}")
    
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write("window.EMBEDDED_ARGUMENTS_DATA = " + json.dumps(bundle, ensure_ascii=False, indent=2) + ";")
    print(f"Saved JS bundle to {js_path}")
