import { Router } from "express";
import { GlintsController } from "../controllers/glints.controller";
import { JobStreetController } from "../controllers/jobstreet.controller";

const router = Router();

/**
 * @route   GET /api/glints
 * @desc    Scrape job listings from Glints
 */
router.get("/glints", GlintsController.scrapeGlints);

/**
 * @route   GET /api/jobstreet
 * @desc    Scrape job listings from JobStreet
 */
router.get("/jobstreet", JobStreetController.scrapeJobStreet);

/**
 * @route   GET /api/health
 * @desc    Health check endpoint
 */
router.get("/health", (req, res) => {
  res.json({
    status: "success",
    message: "Job Scraper API is running",
    version: "2.0.0",
  });
});

export default router;
