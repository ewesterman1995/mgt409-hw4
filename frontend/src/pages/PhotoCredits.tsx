import { PHOTO_CREDITS } from '../photoCredits'

// Attribution for the campus photos, as their Creative Commons licenses require.
export default function PhotoCredits() {
  return (
    <section className="credits">
      <h1>Photo credits</h1>
      <p>
        Campus photos and the Block Y logo are from Wikimedia Commons and used under the
        licenses below. Product photos are Campus Customs' own. Yale marks are trademarks
        of Yale University.
      </p>
      <ul>
        {PHOTO_CREDITS.map((c) => (
          <li key={c.file}>
            <img src={c.file} alt="" loading="lazy" />
            <div>
              <strong>{c.usedFor}</strong>
              <br />
              <a href={c.source} target="_blank" rel="noreferrer">
                {c.title}
              </a>{' '}
              by {c.artist},{' '}
              {c.licenseUrl ? (
                <a href={c.licenseUrl} target="_blank" rel="noreferrer">
                  {c.license}
                </a>
              ) : (
                c.license
              )}
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
