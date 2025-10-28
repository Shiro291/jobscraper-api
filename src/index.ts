import express, { Application } from "express";
import cors from "cors";
import helmet from "helmet";
import morgan from "morgan";
import dotenv from "dotenv";
import router from "./routes";
import { errorHandler, notFoundHandler } from "./middleware/error.middleware";

// Load environment variables
dotenv.config();

const app: Application = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(helmet());
app.use(
  cors({
    origin: process.env.CORS_ORIGIN || "*",
    credentials: true,
  }),
);
app.use(morgan("dev"));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Root route - redirect to /api
app.get("/", (req, res) => {
  res.redirect("/api");
});

// API info route
app.get("/api", (req, res) => {
  res.json({
    message: "Welcome to Job Scraper API",
    version: process.env.API_VERSION || "2.0.0",
    runtime: "Bun",
    endpoints: {
      glints: "/api/glints",
      jobstreet: "/api/jobstreet",
      remoteok: "/api/remoteok",
      indeed: "/api/indeed",
      disnaker_bandung: "/api/disnaker_bandung",
      devjobscanner: "/api/devjobscanner",
      health: "/api/health",
    },
  });
});

// API routes
app.use("/api", router);

// Error handling
app.use(notFoundHandler);
app.use(errorHandler);

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Job Scraper API is running on http://localhost:${PORT}`);
  console.log(`📚 API endpoints available at http://localhost:${PORT}/api`);
});

export default app;
