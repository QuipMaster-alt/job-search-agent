// Import the rendercv function and all the refactored components
#import "@preview/rendercv:0.3.0": *

// Apply the rendercv template with custom configuration
#show: rendercv.with(
  name: "Luis Martinez",
  title: "Luis Martinez - CV",
  footer: context { [#emph[Luis Martinez -- #str(here().page())\/#str(counter(page).final().first())]] },
  top-note: [ #emph[Last updated in May 2026] ],
  locale-catalog-language: "en",
  text-direction: ltr,
  page-size: "us-letter",
  page-top-margin: 0.7in,
  page-bottom-margin: 0.7in,
  page-left-margin: 0.7in,
  page-right-margin: 0.7in,
  page-show-footer: true,
  page-show-top-note: true,
  colors-body: rgb(0, 0, 0),
  colors-name: rgb(0, 79, 144),
  colors-headline: rgb(0, 79, 144),
  colors-connections: rgb(0, 79, 144),
  colors-section-titles: rgb(0, 79, 144),
  colors-links: rgb(0, 79, 144),
  colors-footer: rgb(128, 128, 128),
  colors-top-note: rgb(128, 128, 128),
  typography-line-spacing: 0.6em,
  typography-alignment: "justified",
  typography-date-and-location-column-alignment: right,
  typography-font-family-body: "Source Sans 3",
  typography-font-family-name: "Source Sans 3",
  typography-font-family-headline: "Source Sans 3",
  typography-font-family-connections: "Source Sans 3",
  typography-font-family-section-titles: "Source Sans 3",
  typography-font-size-body: 10pt,
  typography-font-size-name: 30pt,
  typography-font-size-headline: 10pt,
  typography-font-size-connections: 10pt,
  typography-font-size-section-titles: 1.4em,
  typography-small-caps-name: false,
  typography-small-caps-headline: false,
  typography-small-caps-connections: false,
  typography-small-caps-section-titles: false,
  typography-bold-name: true,
  typography-bold-headline: false,
  typography-bold-connections: false,
  typography-bold-section-titles: true,
  links-underline: false,
  links-show-external-link-icon: false,
  header-alignment: center,
  header-photo-width: 3.5cm,
  header-space-below-name: 0.7cm,
  header-space-below-headline: 0.7cm,
  header-space-below-connections: 0.7cm,
  header-connections-hyperlink: true,
  header-connections-show-icons: true,
  header-connections-display-urls-instead-of-usernames: false,
  header-connections-separator: "",
  header-connections-space-between-connections: 0.5cm,
  section-titles-type: "with_partial_line",
  section-titles-line-thickness: 0.5pt,
  section-titles-space-above: 0.5cm,
  section-titles-space-below: 0.3cm,
  sections-allow-page-break: true,
  sections-space-between-text-based-entries: 0.3em,
  sections-space-between-regular-entries: 1.2em,
  entries-date-and-location-width: 4.15cm,
  entries-side-space: 0.2cm,
  entries-space-between-columns: 0.1cm,
  entries-allow-page-break: false,
  entries-short-second-row: true,
  entries-degree-width: 1cm,
  entries-summary-space-left: 0cm,
  entries-summary-space-above: 0cm,
  entries-highlights-bullet:  "•" ,
  entries-highlights-nested-bullet:  "•" ,
  entries-highlights-space-left: 0.15cm,
  entries-highlights-space-above: 0cm,
  entries-highlights-space-between-items: 0cm,
  entries-highlights-space-between-bullet-and-text: 0.5em,
  date: datetime(
    year: 2026,
    month: 5,
    day: 22,
  ),
)


= Luis Martinez

  #headline([Business Intelligence Executive  | BI Leader with 15+ years of experience in Tech, Education, and Travel. designing and delivering reporting systems that translate complex data into actionable intelligence for executive and cross-functional stakeholders. Proven track record building compliance reporting infrastructure under active regulatory scrutiny, establishing data governance standards, and developing real-time dashboards that drive operational decision-making. Deep practitioner experience across Tableau, Looker, Snowflake, and AI-driven analytics — with a consistent pattern of turning fragmented data into unified, trusted reporting frameworks at scale.])

#connections(
  [#link("mailto:luispmartinez@icloud.com", icon: false, if-underline: false, if-color: false)[#connection-with-icon("envelope")[luispmartinez\@icloud.com]]],
  [#link("tel:+1-312-730-3613", icon: false, if-underline: false, if-color: false)[#connection-with-icon("phone")[(312) 730-3613]]],
  [#link("https://linkedin.com/in/luispablomartinez", icon: false, if-underline: false, if-color: false)[#connection-with-icon("linkedin")[luispablomartinez]]],
  [#link("https://public.tableau.com/app/profile/luis.pablo6724", icon: false, if-underline: false, if-color: false)[#connection-with-icon("chart-bar")[Tableau Public Profile]]],
)


== Experience

#regular-entry(
  [
    #strong[Apple Inc.], Contractor - Client Insights Manager

    - Enterprise Reporting & Governance: Directed analytics strategy and governance for Corporate Travel, Meetings & Events, and Entertainment — designing and maintaining 200+ Tableau dashboards that democratized data access for 100k+ global employees and shifted the organization toward a self-service, data-driven culture.

    - Reporting Automation: Architected a multi-fact data model in Tableau Desktop to automate reporting, converting an 80-hour quarterly manual process into an on-demand suite; freed \~320 hours of analyst capacity annually (valued at \$35k+ in recaptured labor).

    - AI-Driven Data Quality: Spearheaded a data quality initiative utilizing Generative AI (Claude, Gemini) for automated validation; ensured 100\% fidelity in high-stakes reports and identified nuanced anomalies often missed by manual review.

    - Operational Intelligence: Engineered a custom staff-modeling dashboard reconciling actual vs. estimated hours; quantified a 2-FTE staffing deficit, providing data-backed justification to optimize workload distribution and prevent burnout.

    - Team Development: Led and mentored a team of 3 analysts, institutionalizing structured training sessions that increased technical self-sufficiency and reduced reliance on external support for complex visualization needs.

  ],
  [
    Austin, TX

    Aug 2025 – May 2026

    

    10 months

  ],
)

#regular-entry(
  [
    #strong[Austin Independent School District], Director, Data Analytics and Reporting

    - Compliance Reporting: Architected data governance dashboards under active legal scrutiny from a special education compliance lawsuit; built reporting infrastructure meeting state authority requirements, identified training gaps that drove a district-wide remediation program, and established the data framework that served as the functional blueprint for the district's subsequent vendor-procured reporting system.

    - Risk Tracking & Executive Reporting: Developed a strategic monitoring dashboard correlating registration trends with historical campus performance — creating a single source of truth that unified C-suite leaders across Enrollment, Technology, and Communications, escalated to the Superintendent and Board for action.

    - Data Quality: Project managed a Snowflake initiative to automate data cleaning of student assessment records; decreased errors by 95\%.

  ],
  [
    Austin, TX

    Jan 2024 – Aug 2025

    

    1 year 8 months

  ],
)

#regular-entry(
  [
    #strong[Texas Education Agency], Manager, Data Fellows Program

    - Power BI Program Leadership: Directed the statewide launch of a Power BI training program serving 200+ districts; implemented and taught DAX, Power Query (M), row-level security, and data modeling best practices — achieving a 95\% satisfaction rate and empowering districts to build campus turnaround plans from data.

    - Standards & Governance: Established agency-wide BI standards via cross-functional workshops — decreasing dashboard build time by 75\% while achieving 100\% parity with legacy system reporting; managed a \$15M program budget.

  ],
  [
    Austin, TX

    Mar 2022 – Jan 2024

    

    1 year 11 months

  ],
)

#regular-entry(
  [
    #strong[Texas Higher Education Coordinating Board], Program Director

    - Dashboard Launch & Optimization: Architected and launched an interactive reporting suite for Texas's statewide strategic plan; gathered requirements and synthesized feedback from 120+ executives to retool dashboards iteratively — directly informing grant award decisions and leading institutions to increase performance targets by as much as 50\%.

    - Reporting Infrastructure: Standardized the BI lifecycle via a Tableau Center of Excellence, accelerating project delivery timelines by 66\% and eliminating agency dependence on manual spreadsheet-based reporting.

  ],
  [
    Austin, TX

    Aug 2017 – Mar 2022

    

    4 years 8 months

  ],
)

#regular-entry(
  [
    #strong[Virtuin], Owner & Lead Consultant

    - Stakeholder Intelligence: Delivered market research that led Texas A&M School of Law to launch a new certificate program, creating a net-new revenue stream — translating complex data into a clear go\/no-go business decision for non-technical leadership.

    - Business Performance: Founded a market research firm generating 50.7\% gross profit margins in the first three years.

  ],
  [
    Chicago, IL

    May 2010 – Aug 2017

    

    7 years 4 months

  ],
)

== Education

#education-entry(
  [
    #strong[DePaul University], Entrepreneurship

  ],
  [
    Chicago, IL

    Sept 2008 – June 2010

  ],
  degree-column: [
    #strong[MBA]
  ],
)

#education-entry(
  [
    #strong[DePaul University], Communications

  ],
  [
    Chicago, IL

    Jan 2002 – June 2004

  ],
  degree-column: [
    #strong[BA]
  ],
)

== Skills

#strong[Reporting & Visualization:] Tableau, Looker, Power BI — dashboard design, real-time reporting, KPI tracking

#strong[Data Management:] Snowflake, SQL, data modeling, data governance, data quality

#strong[Programming & Automation:] R, Python, reporting automation

#strong[AI & Analytics:] Generative AI (Claude, Gemini), predictive modeling, statistical analysis

#strong[Team Leadership:] cross-functional collaboration, mentorship, training program development, \$15M budget management

#strong[Governance & Compliance:] Compliance reporting frameworks, regulatory reporting, state authority reporting, data quality standards
