# Documentation

Comprehensive documentation for the IBCo Vallejo Console project.

## Documentation Structure

```
docs/
├── architecture/        # System design and architecture
├── data_sources/        # Data source guides
├── methodology/         # Analysis methodology
├── operations/          # Deployment and operations
├── user_guides/         # End-user documentation
└── legal/              # Legal and compliance docs
```

## Documentation Categories

### Architecture Documentation

**Purpose**: Technical design decisions and system architecture

**Location**: `architecture/`

**Contents**:
- System design overview
- Database schema and design
- API design and endpoints
- Data pipeline architecture
- Technology stack decisions

**Audience**: Developers, technical contributors

### Data Sources Documentation

**Purpose**: Understanding where data comes from and how to interpret it

**Location**: `data_sources/`

**Contents**:
- Comprehensive data source catalog
- CAFR reading guide
- CalPERS data interpretation
- State Controller data guide
- Data validation procedures

**Audience**: Data contributors, analysts, researchers

### Methodology Documentation

**Purpose**: Transparent explanation of analysis methods

**Location**: `methodology/` (also see [../METHODOLOGY.md](../METHODOLOGY.md))

**Contents**:
- Risk scoring methodology
- Projection methodology
- Validation methodology
- Peer comparison approach
- Assumptions and limitations

**Audience**: All users, especially those evaluating data quality

### Operations Documentation

**Purpose**: Deploying, running, and maintaining the platform

**Location**: `operations/`

**Contents**:
- Deployment guide
- Operations runbook
- Backup and recovery procedures
- Monitoring and alerting
- Incident response

**Audience**: DevOps, system administrators

### User Guides

**Purpose**: How to use the platform and interpret results

**Location**: `user_guides/`

**Contents**:
- User guide for web interface
- API usage guide
- Frequently asked questions
- Interpreting risk scores
- Data download and export

**Audience**: End users, researchers, journalists, residents

### Legal Documentation

**Purpose**: Legal disclaimers, licenses, and compliance

**Location**: `legal/` (also see [../DISCLAIMER.md](../DISCLAIMER.md))

**Contents**:
- Detailed legal disclaimer
- Data licensing information
- Privacy policy
- Terms of service
- MSRB compliance

**Audience**: All users, especially legal/compliance review

## Documentation Standards

### Writing Style

- **Clear and concise**: Use plain language
- **Assume beginner knowledge**: Explain technical terms
- **Provide examples**: Show, don't just tell
- **Link related docs**: Help users navigate
- **Keep updated**: Document reflects current implementation

### Markdown Standards

- Use GitHub-flavored Markdown
- Include table of contents for long docs
- Use code blocks with language specification
- Include diagrams where helpful (use Mermaid or ASCII)
- Link to related documentation

### Documentation Templates

See [templates/](templates/) for:
- Architecture decision record (ADR) template
- User guide template
- API documentation template
- Runbook template

## Contributing to Documentation

Documentation contributions are highly valued!

### How to Contribute

1. **Identify gap**: What's missing or unclear?
2. **Write or update**: Follow style guide
3. **Review**: Check for accuracy and clarity
4. **Submit PR**: Include documentation changes in pull request

### Documentation Review

All documentation should be reviewed for:
- **Accuracy**: Is it technically correct?
- **Clarity**: Can a beginner understand it?
- **Completeness**: Does it cover the topic fully?
- **Currency**: Is it up-to-date with current code?

## Documentation Builds

### Local Preview

Preview documentation locally:

```bash
# Install MkDocs
poetry install --with dev

# Serve docs locally
poetry run mkdocs serve

# Open browser to http://localhost:8000
```

### Publishing

Documentation is automatically published to:
- GitHub Pages: https://ibco-ca.github.io/vallejo-ibco-ca/
- Main website: https://docs.ibco-ca.us/

## Documentation Roadmap

### Phase 1: Foundation (Current)
- [x] Project README
- [x] Methodology document
- [x] Legal disclaimer
- [x] Contributing guide
- [ ] Basic architecture overview
- [ ] Initial user guide

### Phase 2: Technical Depth
- [ ] Detailed API documentation
- [ ] Database schema documentation
- [ ] Data pipeline architecture
- [ ] Deployment guide
- [ ] Operations runbook

### Phase 3: User-Focused
- [ ] Comprehensive user guide
- [ ] Video tutorials
- [ ] Data interpretation guide
- [ ] FAQ expansion
- [ ] Case studies

### Phase 4: Advanced
- [ ] Developer tutorials
- [ ] Contributing walkthrough
- [ ] Advanced API usage
- [ ] Custom integration examples
- [ ] Research methodology papers

## Documentation Tools

### Recommended Tools

- **MkDocs**: Static site generator
- **MkDocs Material**: Beautiful theme
- **Mermaid**: Diagrams in Markdown
- **PlantUML**: Architecture diagrams
- **Swagger/OpenAPI**: API documentation

### Diagrams

Create diagrams using:
- Mermaid (for flowcharts, sequences)
- PlantUML (for UML diagrams)
- Draw.io (for complex visualizations)

Store diagram source files in `diagrams/` directory.

## Questions & Feedback

### How to Get Help

- **General questions**: Open GitHub Discussion
- **Documentation issues**: Open GitHub Issue with "documentation" label
- **Suggestions**: Email docs@ibco-ca.us

### Documentation Issues

Report issues with:
- Broken links
- Outdated information
- Unclear explanations
- Missing topics

Use the "documentation" label on GitHub issues.

## License

All documentation is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) unless otherwise noted.

You are free to:
- Share: Copy and redistribute
- Adapt: Remix and build upon

Under these terms:
- Attribution: Give appropriate credit
- No additional restrictions

---

**Last Updated**: 2025-01-10

For questions: docs@ibco-ca.us
