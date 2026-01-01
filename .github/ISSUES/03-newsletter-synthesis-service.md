# Implement Newsletter Synthesis Service

**Labels**: `feature`, `ai`, `core-functionality`, `high-priority`

## Overview
Create a service that combines Brave Search results with Anthropic Deep Research to synthesize comprehensive, fact-based newsletters.

## Objectives
- Implement `synthesize_newsletter()` function in `app/services.py`
- Orchestrate both Brave Search and Anthropic API
- Combine web research with AI analysis
- Use Claude to synthesize findings into cohesive newsletter
- Ensure factual accuracy with source attribution

## Technical Requirements

### Orchestration Flow
1. **Research Phase**
   - [ ] Execute Brave Search for topic keywords
   - [ ] Extract key information from search results
   - [ ] Run Anthropic Deep Research on topic
   - [ ] Run both operations in parallel (async)

2. **Synthesis Phase**
   - [ ] Feed search results + research into Claude
   - [ ] Prompt Claude to synthesize findings
   - [ ] Include source attribution and citations
   - [ ] Format as newsletter with sections

3. **Quality Assurance**
   - [ ] Validate factual claims against sources
   - [ ] Ensure diverse perspectives included
   - [ ] Check for bias or unbalanced coverage
   - [ ] Verify all links are valid

### Implementation Details

```python
def synthesize_newsletter(topic: str, search_results: List[Dict], research_output: str) -> Dict:
    """
    Synthesize newsletter from Brave search and Anthropic research.

    Workflow:
    1. Format search results for context
    2. Combine with deep research output
    3. Use Claude to synthesize comprehensive newsletter
    4. Add source attributions

    Args:
        topic: Newsletter topic
        search_results: Results from Brave Search
        research_output: Output from Anthropic Deep Research

    Returns:
        dict: Synthesized newsletter with subject, content, sources
    """
```

### Synthesis Strategy
- [ ] Create structured prompt for Claude combining both sources
- [ ] Instruct Claude to:
  - Cross-reference search results with research
  - Identify key themes and insights
  - Provide balanced coverage
  - Include specific examples and data points
  - Cite sources for claims
  - Organize into logical sections

### Output Format
- [ ] Subject line (engaging, SEO-friendly)
- [ ] Executive summary (2-3 sentences)
- [ ] Main content sections (3-5 sections):
  - Section title
  - Content (200-300 words each)
  - Key statistics/data points
  - Source citations
- [ ] Key takeaways (3-5 bullet points)
- [ ] Further reading (links from search results)
- [ ] Newsletter metadata (topic, generated_at, sources_count)

### Error Handling
- [ ] Handle partial failures (search fails but research succeeds)
- [ ] Fallback to research-only or search-only modes
- [ ] Log synthesis quality metrics
- [ ] Detect and handle low-quality synthesis

### Testing
- [ ] Unit tests for synthesis logic
- [ ] Test with various topic types (news, tech, science, business)
- [ ] Test fallback scenarios
- [ ] Validate output structure
- [ ] Check source attribution accuracy
- [ ] Integration test end-to-end workflow

### Performance
- [ ] Parallel API calls (search + research)
- [ ] Caching intermediate results
- [ ] Track synthesis time metrics
- [ ] Optimize token usage

## Example Implementation

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def synthesize_newsletter(topic: str, search_results: List[Dict] = None, research_output: str = None) -> Dict:
    """Synthesize newsletter from multiple sources."""

    # If sources not provided, fetch them in parallel
    if search_results is None or research_output is None:
        with ThreadPoolExecutor(max_workers=2) as executor:
            search_future = executor.submit(search_brave, topic, num_results=10)
            research_future = executor.submit(generate_newsletter_content, topic)

            search_results = search_future.result()
            research_output = research_future.result()

    # Format search context
    search_context = format_search_results(search_results)

    # Synthesis prompt
    synthesis_prompt = f"""
You are synthesizing a comprehensive newsletter about: {topic}

RESEARCH FINDINGS:
{research_output['content']}

WEB SEARCH RESULTS:
{search_context}

Please synthesize these sources into a cohesive, well-structured newsletter.

Requirements:
1. Cross-reference information between sources
2. Identify key themes and insights
3. Include specific data points with citations
4. Organize into 3-5 clear sections
5. Add an executive summary
6. List key takeaways
7. Cite sources using [1], [2] notation

Format as JSON with: subject, summary, sections[], takeaways[], sources[]
"""

    # Use Claude for synthesis
    client = Anthropic(api_key=current_app.config['ANTHROPIC_API_KEY'])
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=6000,
        messages=[{"role": "user", "content": synthesis_prompt}]
    )

    # Parse and validate synthesis
    newsletter = parse_synthesis_response(response.content)
    newsletter['metadata'] = {
        'topic': topic,
        'generated_at': datetime.utcnow().isoformat(),
        'sources_count': len(search_results),
        'research_used': bool(research_output)
    }

    return newsletter
```

## Acceptance Criteria
- [ ] Synthesis successfully combines both sources
- [ ] Output is well-structured and readable
- [ ] Sources are properly cited
- [ ] Parallel execution works correctly
- [ ] Fallback modes functional
- [ ] Tests achieve >80% coverage
- [ ] Documentation complete
- [ ] Performance under 30 seconds for synthesis

## Related Issues
- Depends on: #01 (Anthropic API), #02 (Brave Search)
- Blocks: None

## Estimated Effort
Medium-Large (2-3 days)
