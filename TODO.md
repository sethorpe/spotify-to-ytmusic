# Project TODO

Track future enhancements and bug fixes for the Spotify to YouTube Music migrator.

## [DONE] Completed (MVP)

- [x] Project setup with Poetry
- [x] Data models (Track, Playlist, Album, MigrationResult)
- [x] Spotify API integration (authentication, playlist fetching)
- [x] YouTube Music API integration (authentication, playlist creation)
- [x] Smart track matching (ISRC + fuzzy search)
- [x] CLI interface with Click
- [x] Single playlist migration
- [x] Bulk playlist migration
- [x] Migration reporting
- [x] Documentation (README, USAGE, QUICKSTART, DEVELOPMENT)

## [IN PROGRESS] In Progress

None currently

## [PLANNED] Planned Features

### High Priority

- [ ] **Album Migration**
  - Implement `migrate-album` command
  - Add album search/matching logic
  - Handle album vs playlist differences in YT Music

- [ ] **Better Error Handling**
  - Retry logic for failed track searches
  - Rate limit detection and automatic backoff
  - Better error messages with suggested fixes

- [ ] **Progress Indicators**
  - Use tqdm for progress bars
  - Show estimated time remaining
  - Better visual feedback during long migrations

### Medium Priority

- [ ] **Migration Reports**
  - Export results to CSV/JSON
  - Save failed tracks list for manual review
  - Generate summary statistics

- [ ] **Configuration Management**
  - Config file for settings (retries, timeout, etc.)
  - Multiple profile support
  - Save preferences

- [ ] **Improved Matching**
  - Better fuzzy matching algorithm
  - Match by duration as additional factor
  - User confirmation for uncertain matches

- [ ] **Logging System**
  - Add proper logging with loguru
  - Separate log files for each migration
  - Verbose/debug mode

### Low Priority

- [ ] **Interactive Mode**
  - TUI (Terminal UI) with keyboard navigation
  - Select playlists from a list
  - Preview migration before execution

- [ ] **Playlist Management**
  - Update existing playlists instead of creating new ones
  - Delete/manage YT Music playlists from CLI
  - Sync changes (add new tracks to existing playlist)

- [ ] **Advanced Features**
  - Reverse migration (YT Music -> Spotify)
  - Cross-platform sync
  - Scheduled migrations
  - Playlist deduplication

## [FUTURE] Future: Web Application

When ready to build a web version:

### Phase 1: Basic Web UI
- [ ] Choose web framework (Flask vs FastAPI)
- [ ] Create basic frontend (React or Vue)
- [ ] OAuth integration for web
- [ ] Simple playlist migration interface

### Phase 2: Enhanced Features
- [ ] User accounts and saved migrations
- [ ] Migration history
- [ ] Batch operations UI
- [ ] Progress tracking in real-time

### Phase 3: Monetization/Open Source
- [ ] Decide on business model
- [ ] Set up hosting infrastructure
- [ ] Add analytics
- [ ] Create landing page
- [ ] Launch beta

## [KNOWN ISSUES] Known Issues

Currently none reported.

## [IDEAS] Ideas for Consideration

- **Multi-platform support**: Add Apple Music, Tidal, Deezer
- **Collaborative playlists**: Handle collaborative playlist permissions
- **Playlist backup**: Export playlists to JSON for backup
- **Smart playlists**: Migrate based on rules/filters
- **Playlist merging**: Combine multiple playlists
- **Music discovery**: Suggest similar tracks if original not found

## [METRICS] Metrics to Track

Once deployed:
- [ ] Total playlists migrated
- [ ] Average success rate
- [ ] Most common failure reasons
- [ ] User retention
- [ ] API quota usage

## [NEXT STEPS] Next Steps (Immediate)

1. **Test the MVP thoroughly**
   - Test with various playlist sizes
   - Test with different music genres
   - Test error scenarios

2. **Gather user feedback**
   - Use it yourself for a week
   - Note any pain points
   - Identify most-needed features

3. **Prioritize next features**
   - Based on feedback
   - Based on ease of implementation
   - Based on impact

## [NOTES] Notes

- Keep the CLI lean and fast
- Prioritize reliability over features
- Document everything as you go
- Test with real playlists before each release

---

**Last Updated**: November 6, 2025
**Current Version**: 0.1.0 (MVP)
**Status**: Proof of Concept Complete
