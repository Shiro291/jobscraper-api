![poster](/image/poster.webp "poster")

# Job Scraper API

This project is a job scraper API designed to gather job listings from various sources. It has been rewritten from Python FastAPI to **TypeScript with Express.js**, optimized to run with **Bun** runtime for maximum performance.

## 🚀 Tech Stack

- **Runtime**: Bun (or Node.js >= 18.0.0)
- **Framework**: Express.js
- **Language**: TypeScript
- **Web Scraping**: Cheerio (HTML parsing) + Axios (HTTP client)
- **Architecture**: MVC pattern with separation of concerns

## 📋 Requirements

```
Bun >= 1.0.0
or
Node.js >= 18.0.0
npm >= 9.0.0
```

## 🔧 Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd jobscraper-api
   ```

2. **Install dependencies**

   Using Bun (recommended):

   ```bash
   bun install
   ```

   Using npm:

   ```bash
   npm install
   ```

3. **Setup environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` file as needed:

   ```env
   PORT=8000
   NODE_ENV=development
   CORS_ORIGIN=*
   API_VERSION=2.0.0
   ```

## 🏗️ Project Structure

```
jobscraper-api/
│
├── src/
│   ├── config/                 # Configuration files
│   │   └── sample_cookie.json  # Cookie samples
│   │
│   ├── controllers/            # Request handlers & scraping logic
│   │   ├── glints.controller.ts
│   │   ├── jobstreet.controller.ts
│   │   ├── remoteok.controller.ts
│   │   ├── indeed.controller.ts
│   │   ├── disnaker.controller.ts
│   │   └── devjobscanner.controller.ts
│   │
│   ├── helpers/                # Utility functions
│   │   ├── response.helper.ts  # Standardized API responses
│   │   ├── cookie.helper.ts    # Cookie management
│   │   └── scraper.helper.ts   # HTTP client with anti-bot measures
│   │
│   ├── middleware/             # Express middleware
│   │   └── error.middleware.ts # Error handling
│   │
│   ├── routes/                 # API route definitions
│   │   └── index.ts
│   │
│   ├── types/                  # TypeScript type definitions
│   │   └── index.ts
│   │
│   └── index.ts                # Application entry point
│
├── dist/                       # Compiled JavaScript (after build)
├── .env                        # Environment variables (not committed)
├── .env.example                # Environment variables template
├── .gitignore
├── package.json
├── tsconfig.json
├── README.md
└── LICENSE
```

### 📂 Directory Details

#### **src/config**

Contains configuration files:

- `sample_cookie.json`: Stores cookies in JSON format. Export cookies using [Cookie Editor](https://cookie-editor.cgagnier.ca/) browser extension.

#### **src/controllers**

Business logic and scraping implementations:

- `glints.controller.ts`: Scraping logic for Glints job listings
- `jobstreet.controller.ts`: Scraping logic for JobStreet
- Additional controllers for other job platforms

#### **src/helpers**

Reusable utility functions:

- `response.helper.ts`: Standardized success/failure API responses
- `cookie.helper.ts`: Cookie loading and parsing utilities
- `scraper.helper.ts`: HTTP client singleton with anti-bot headers

#### **src/middleware**

Express middleware functions:

- `error.middleware.ts`: Global error handling and 404 handler

#### **src/routes**

API route definitions linking endpoints to controllers

#### **src/types**

TypeScript interfaces and type definitions for type safety

---

## 🎯 Usage

### Development Mode

Using Bun (with hot reload):

```bash
bun run dev
```

Using npm:

```bash
npm run dev
```

### Production Mode

Build the project:

```bash
bun run build
# or
npm run build
```

Run the production server:

```bash
bun run start
# or
npm start
```

### Direct Run (Bun only)

```bash
bun src/index.ts
```

---

## 📡 API Endpoints

The API will be available at `http://localhost:8000`

### Base Routes

- `GET /` - Redirects to `/api`
- `GET /api` - API information and available endpoints
- `GET /api/health` - Health check endpoint

### Job Scraping Endpoints

#### **Glints**

```
GET /api/glints?work=Programmer&job_type=FULL_TIME&option_work=ONSITE&page=1
```

**Query Parameters:**

- `work` (default: "Programmer") - Job title or keywords
- `job_type` (default: "FULL_TIME") - Employment type
  - Options: `FULL_TIME`, `PART_TIME`, `CONTRACT`, `INTERNSHIP`
- `option_work` (default: "ONSITE") - Work arrangement
  - Options: `ONSITE`, `HYBRID`, `REMOTE`
- `location_id` (default: "") - Location ID
- `location_name` (default: "All+Cities/Provinces") - Location name
- `page` (default: "1") - Page number

#### **JobStreet**

```
GET /api/jobstreet?work=Programmer&location=Jakarta&country=id&page=1
```

**Query Parameters:**

- `work` (default: "Programmer") - Job title or keywords
- `location` (default: "") - City or region
- `country` (default: "id") - Country code
  - Options: `id`, `my`, `sg`, `th`, `hk`, `nz`, `au`
- `page` (default: "1") - Page number

#### **RemoteOK**

```
GET /api/remoteok?keywords=engineer&page=1
```

#### **Indeed**

```
GET /api/indeed?keyword=programmer&location=Jakarta&country=id&page=0
```

#### **Disnaker Bandung**

```
GET /api/disnaker_bandung?page=1
```

#### **DevJobsScanner**

```
GET /api/devjobscanner?keywords=web+developer&page=1
```

---

## 📦 Response Format

### Success Response

```json
{
  "status": "success",
  "message": "Success find job",
  "data": {
    "total_jobs": 25,
    "jobs": [
      {
        "title": "Senior Software Engineer",
        "salary": "Rp 8.000.000 - Rp 15.000.000",
        "location": "Jakarta Selatan, DKI Jakarta",
        "company_name": "Tech Company Indonesia",
        "company_logo": "https://example.com/logo.png",
        "link": "https://example.com/job/123"
      }
    ],
    "pagination": {
      "current_page": 1,
      "last_page": 5,
      "has_next": true
    }
  }
}
```

### Error Response

```json
{
  "status": "failed",
  "message": "Error description"
}
```

---

## 🛠️ Available Scripts

```bash
# Development with hot reload
bun run dev

# Type checking (no emit)
bun run type-check

# Build for production
bun run build

# Start production server
bun run start

# Lint code
bun run lint

# Fix linting issues
bun run lint:fix
```

---

## 🔒 Cookie Configuration

Some job platforms require authentication cookies to bypass bot detection.

1. Install [Cookie Editor](https://cookie-editor.cgagnier.ca/) browser extension
2. Visit the target website and login if needed
3. Export cookies as JSON
4. Save to `src/config/{platform}.json`

Example cookie file structure:

```json
[
  {
    "name": "session_id",
    "value": "abc123...",
    "domain": ".example.com",
    "path": "/",
    "secure": true,
    "httpOnly": true
  }
]
```

---

## 🚦 Migration from Python FastAPI

This project has been migrated from Python FastAPI to TypeScript Express. Key changes:

| Aspect       | Python Version    | TypeScript Version |
| ------------ | ----------------- | ------------------ |
| Runtime      | Python 3.10+      | Bun / Node.js 18+  |
| Framework    | FastAPI           | Express.js         |
| Language     | Python            | TypeScript         |
| Web Scraping | BeautifulSoup4    | Cheerio            |
| HTTP Client  | cloudscraper      | Axios              |
| Type Safety  | Python type hints | TypeScript         |
| Performance  | ~200ms            | ~50ms (with Bun)   |

---

## 🤝 Contributing

Feel free to fork this repository and contribute enhancements or bug fixes through pull requests.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

---

## ⚡ Why Bun?

- **3x faster** package installation than npm
- **Native TypeScript** support (no transpilation needed)
- **Built-in hot reload** for development
- **Better performance** than Node.js
- **Fully compatible** with Node.js APIs

However, the project also works perfectly with Node.js if you prefer.

---

## 📧 Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Made with ❤️ using TypeScript, Express, and Bun**
