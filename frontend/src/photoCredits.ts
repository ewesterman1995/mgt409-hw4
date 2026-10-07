// Campus photos and the Block Y logo from Wikimedia Commons, used under their free
// licenses. Shown on the Photo credits page (required by the Creative Commons licenses).

export interface PhotoCredit {
  file: string
  usedFor: string
  title: string
  artist: string
  license: string
  licenseUrl: string
  source: string
}

export const PHOTO_CREDITS: PhotoCredit[] = [
  {
    "file": "/campus/hero.jpg",
    "usedFor": "Home page banner",
    "title": "Yale University Cheerleaders",
    "artist": "Kenneth Zirkel",
    "license": "CC BY-SA 3.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/3.0",
    "source": "https://commons.wikimedia.org/wiki/File:Yale_University_Cheerleaders.jpg"
  },
  {
    "file": "/campus/classic.jpg",
    "usedFor": "Classic Yale collection",
    "title": "Yale Old Campus (4139296788)",
    "artist": "Francisco Anzola",
    "license": "CC BY 2.0",
    "licenseUrl": "https://creativecommons.org/licenses/by/2.0",
    "source": "https://commons.wikimedia.org/wiki/File:Yale_Old_Campus_(4139296788).jpg"
  },
  {
    "file": "/campus/colleges.jpg",
    "usedFor": "Residential Colleges collection",
    "title": "Branford Court spring",
    "artist": "Nick Allen",
    "license": "CC BY-SA 3.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/3.0",
    "source": "https://commons.wikimedia.org/wiki/File:Branford_Court_spring.JPG"
  },
  {
    "file": "/campus/schools.jpg",
    "usedFor": "Graduate & Professional Schools collection",
    "title": "Sterling Law Building, Yale Law School",
    "artist": "Kenneth C. Zirkel",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
    "source": "https://commons.wikimedia.org/wiki/File:Sterling_Law_Building,_Yale_Law_School.jpg"
  },
  {
    "file": "/campus/athletics.jpg",
    "usedFor": "Yale Athletics collection",
    "title": "2019 Yale Bulldogs football players",
    "artist": "Kenneth Zirkel",
    "license": "CC BY-SA 3.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/3.0",
    "source": "https://commons.wikimedia.org/wiki/File:2019_Yale_Bulldogs_football_players.jpg"
  },
  {
    "file": "/campus/family.jpg",
    "usedFor": "Yale Family collection and home page banner",
    "title": "Yale FES caps",
    "artist": "Dicklyon",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
    "source": "https://commons.wikimedia.org/wiki/File:Yale_FES_caps.jpg"
  },
  {
    "file": "/campus/about.jpg",
    "usedFor": "About Us page and home page banner",
    "title": "Branford harkness",
    "artist": "Anthony Tokman",
    "license": "CC BY-SA 4.0",
    "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
    "source": "https://commons.wikimedia.org/wiki/File:Branford_harkness.jpg"
  },
  {
    "file": "/block-y.svg",
    "usedFor": "Logo in the header and browser tab",
    "title": "Old Yale Bulldogs athletics logo (Yale Athletics Block Y)",
    "artist": "Yale University (trademark of Yale University)",
    "license": "Public domain (copyright); trademark used for this Yale class project",
    "licenseUrl": "",
    "source": "https://commons.wikimedia.org/wiki/File:Old_Yale_Bulldogs_athletics_logo.svg"
  }
]
