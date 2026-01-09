<!--
DOCUMENTATION SCOPE: This file contains the historical context, research, and decisions that led to the current architecture.
-->

# Decisions & Risks

## Research Summary

Comparison of existing projects that influenced this design:

| Project | Key Strengths | Key Weaknesses |
|---------|---------------|----------------|
| **khengyun/notebooklm-mcp** | Production-ready, Pydantic v2 | Fewer features |
| **jacob-bd/notebooklm-mcp** | Complete feature set, RPC details | Weak typing |
| **PleasePrompto** | Session continuity patterns | No content generation |

### Decisions
1.  **FastMCP & Pydantic V2**: Adopted from `khengyun` for robust typing.
2.  **31-Tool Inventory**: Adopted from `jacob-bd` to ensure completeness.
3.  **Playwright**: Chosen over Selenium for better async support and reliability.

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **API Changes** | High | The API is internal. We run daily CI tests against the real NotebookLM to detect breakage immediately. |
| **Cookie Expiry** | Medium | Cookies last 2-4 weeks. The CLI provides `auth check` and clear re-login prompts. |
| **Rate Limiting** | Medium | Requests are cached where possible, and exponential backoff is used for retries. |
| **Verification** | High | All features are verified with both automated integration tests and manual CLI commands. |

## Future Decision Points
**After Phase 2**: Evaluate API stability. If RPCs change too frequently, consider forking `jacob-bd`'s approach or contributing back to it, though our current strict-typing approach provides safer maintenance.

## References

- **jacob-bd/notebooklm-mcp**: https://github.com/jacob-bd/notebooklm-mcp (tools, RPC protocol)
- **khengyun/notebooklm-mcp**: https://github.com/khengyun/notebooklm-mcp (architecture, testing)
- **Podcastfy**: https://github.com/souzatharsis/podcastfy (async patterns)
- **Playwright docs**: https://playwright.dev/python/docs/intro
- **Pydantic v2 docs**: https://docs.pydantic.dev/latest/
