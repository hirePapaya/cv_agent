/* global React */
const { Fragment } = React;

// ---- shared small pieces ----
function ContactInline({ items, sep }) {
  return (
    <div className="cv-contact-inline">
      {items.map((c, i) => (
        <span key={c.label} className="cv-contact-item">
          {i > 0 && <span className="cv-dot">{sep || "·"}</span>}
          <a href={c.href}>{c.label}</a>
        </span>
      ))}
    </div>
  );
}

function ExperienceEntry({ job, compact }) {
  return (
    <div className={"cv-job" + (compact ? " cv-job--compact" : "")}>
      <div className="cv-job-head">
        <span className="cv-job-co">{job.company}</span>
        <span className="cv-job-dates">{job.dates}</span>
      </div>
      <div className="cv-job-sub">
        <span className="cv-job-role">{job.role}</span>
        {job.location && <span className="cv-job-loc">{job.location}</span>}
      </div>
      <ul className="cv-bullets">
        {job.bullets.map((b, i) => (
          <li key={i}>{b}</li>
        ))}
      </ul>
    </div>
  );
}

function SectionTitle({ children }) {
  return <h2 className="cv-section-title">{children}</h2>;
}

// =====================================================================
// VARIATION A — single-column editorial
// =====================================================================
function ResumeA({ data }) {
  const R = data || window.RESUME;
  return (
    <div className="cv cv-a">
      <header className="cv-a-header">
        <h1 className="cv-name">{R.name}</h1>
        <p className="cv-title">{R.title}</p>
        <ContactInline items={R.contact} />
      </header>

      <section className="cv-block">
        <SectionTitle>Professional summary</SectionTitle>
        <p className="cv-summary">{R.summary}</p>
      </section>

      <section className="cv-block">
        <SectionTitle>Experience</SectionTitle>
        {R.experience.map((job) => (
          <ExperienceEntry key={job.company} job={job} />
        ))}
      </section>

      <div className="cv-a-grid">
        <section className="cv-block">
          <SectionTitle>Education</SectionTitle>
          {R.education.map((e) => (
            <div key={e.school} className="cv-edu">
              <div className="cv-job-head">
                <span className="cv-job-co">{e.school}</span>
                <span className="cv-job-dates">{e.dates}</span>
              </div>
              <div className="cv-job-sub">
                <span className="cv-job-role">{e.degree}</span>
                {e.location && <span className="cv-job-loc">{e.location}</span>}
              </div>
            </div>
          ))}
        </section>

        <section className="cv-block">
          <SectionTitle>Skills</SectionTitle>
          <dl className="cv-skills">
            {R.skills.map((s) => (
              <div key={s.label} className="cv-skill-row">
                <dt>{s.label}</dt>
                <dd>{s.items}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </div>
  );
}

// =====================================================================
// VARIATION B — two-column rail
// =====================================================================
function ResumeB({ data }) {
  const R = data || window.RESUME;
  return (
    <div className="cv cv-b">
      <aside className="cv-b-rail">
        <div className="cv-b-namewrap">
          <h1 className="cv-name">{R.name}</h1>
          <p className="cv-title">{R.title}</p>
        </div>

        <section className="cv-rail-block">
          <SectionTitle>Contact</SectionTitle>
          <ul className="cv-contact-stack">
            {R.contact.map((c) => (
              <li key={c.label}>
                <a href={c.href}>{c.label}</a>
              </li>
            ))}
          </ul>
        </section>

        <section className="cv-rail-block">
          <SectionTitle>Skills</SectionTitle>
          <dl className="cv-skills cv-skills--stack">
            {R.skills.map((s) => (
              <div key={s.label} className="cv-skill-row">
                <dt>{s.label}</dt>
                <dd>{s.items}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="cv-rail-block">
          <SectionTitle>Education</SectionTitle>
          {R.education.map((e) => (
            <div key={e.school} className="cv-edu">
              <div className="cv-edu-school">{e.school}</div>
              <div className="cv-edu-degree">{e.degree}</div>
              <div className="cv-edu-meta">
                {e.location ? e.location + " · " : ""}
                {e.dates}
              </div>
            </div>
          ))}
        </section>
      </aside>

      <main className="cv-b-main">
        <section className="cv-block">
          <SectionTitle>Professional summary</SectionTitle>
          <p className="cv-summary">{R.summary}</p>
        </section>

        <section className="cv-block">
          <SectionTitle>Experience</SectionTitle>
          {R.experience.map((job) => (
            <ExperienceEntry key={job.company} job={job} compact />
          ))}
        </section>
      </main>
    </div>
  );
}

Object.assign(window, { ResumeA, ResumeB });
