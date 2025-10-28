import { Router } from "express";
import { scrapeGlints } from "../controllers/glints.controller";
import { scrapeJobStreet } from "../controllers/jobstreet.controller";
import { scrapeRemoteOK } from "../controllers/remoteok.controller";
import { scrapeIndeed } from "../controllers/indeed.controller";
import { scrapeDisnakerBandung } from "../controllers/disnaker.controller";
import { scrapeDevJobsScanner } from "../controllers/devjobscanner.controller";

const router = Router();

/**
 * @route   GET /api/glints
 * @desc    Scrape job listings from Glints
 * @query   work, job_type, option_work, location_id, location_name, page
 */
router.get("/glints", scrapeGlints);

/**
 * @route   GET /api/jobstreet
 * @desc    Scrape job listings from JobStreet
 * @query   work, location, country, page
 */
router.get("/jobstreet", scrapeJobStreet);

/**
 * @route   GET /api/remoteok
 * @desc    Scrape job listings from RemoteOK
 * @query   keywords, page
 */
router.get("/remoteok", scrapeRemoteOK);

/**
 * @route   GET /api/indeed
 * @desc    Scrape job listings from Indeed
 * @query   keyword, location, country, page
 */
router.get("/indeed", scrapeIndeed);

/**
 * @route   GET /api/disnaker_bandung
 * @desc    Scrape job listings from Disnaker Bandung
 * @query   page
 */
router.get("/disnaker_bandung", scrapeDisnakerBandung);

/**
 * @route   GET /api/devjobscanner
 * @desc    Scrape job listings from DevJobsScanner
 * @query   keywords, page
 */
router.get("/devjobscanner", scrapeDevJobsScanner);

/**
 * @route   GET /api/health
 * @desc    Health check endpoint
 */
router.get("/health", (req, res) => {
  res.json({
    status: "success",
    message: "Job Scraper API is running",
    version: "2.0.0",
    endpoints: {
      glints: "/api/glints",
      jobstreet: "/api/jobstreet",
      remoteok: "/api/remoteok",
      indeed: "/api/indeed",
      disnaker_bandung: "/api/disnaker_bandung",
      devjobscanner: "/api/devjobscanner",
    },
  });
});

export default router;
