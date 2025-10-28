import { Request, Response } from "express";
import * as cheerio from "cheerio";
import { ResponseHelper } from "../helpers/response.helper";
import { ScraperHelper } from "../helpers/scraper.helper";
import { GlintsParams, Job } from "../types";

const VALID_JOB_TYPES = ["FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP"];
const VALID_WORK_OPTIONS = ["ONSITE", "HYBRID", "REMOTE"];
const VALID_LOCATION_NAMES = [
  "All+Cities/Provinces",
  "Jabodetabek",
  "Banten",
  "Jawa Barat",
  "DKI Jakarta",
  "Jakarta Selatan, DKI Jakarta",
  "Jakarta Barat, DKI Jakarta",
  "Tangerang, Banten",
  "Jakarta Utara, DKI Jakarta",
  "Bandung, Jawa Barat",
];
const VALID_LOCATION_IDS = [
  "",
  "JABODETABEK",
  "82f248c3-3fb3-4600-98fe-4afb47d7558d",
  "06c9e480-42e7-4f11-9d6c-67ad64ccc0f6",
  "78d63064-78a1-4577-8516-036a6c5e903e",
  "078b37b2-e791-4739-958e-c29192e5df3e",
  "af0ed74f-1b51-43cf-a14c-459996e39105",
  "ae3c458e-5947-4833-8f1b-e001ce2fad1d",
  "ea61f4ac-5864-4b2b-a2c8-aa744a2aafea",
  "86a3dc56-1bd7-4cd3-8225-d3e4b976e552",
];

export const scrapeGlints = async (
  req: Request,
  res: Response,
): Promise<Response> => {
  const {
    work = "Programmer",
    job_type = "FULL_TIME",
    option_work = "ONSITE",
    location_id = "",
    location_name = "All+Cities/Provinces",
    page = "1",
  } = req.query as GlintsParams;

  // Validasi parameter
  if (!VALID_JOB_TYPES.includes(job_type)) {
    return ResponseHelper.failure(
      res,
      `Invalid job_type: ${job_type}. Valid options: ${VALID_JOB_TYPES.join(", ")}`,
      400,
    );
  }

  if (!VALID_WORK_OPTIONS.includes(option_work)) {
    return ResponseHelper.failure(
      res,
      `Invalid option_work: ${option_work}. Valid options: ${VALID_WORK_OPTIONS.join(", ")}`,
      400,
    );
  }

  if (!VALID_LOCATION_IDS.includes(location_id)) {
    return ResponseHelper.failure(
      res,
      `Invalid location_id: ${location_id}`,
      400,
    );
  }

  if (!VALID_LOCATION_NAMES.includes(location_name)) {
    return ResponseHelper.failure(
      res,
      `Invalid location_name: ${location_name}`,
      400,
    );
  }

  const pageNum = parseInt(page);
  if (isNaN(pageNum) || pageNum <= 0) {
    return ResponseHelper.failure(res, "Page must be a positive integer", 400);
  }

  const url = `https://glints.com/id/opportunities/jobs/explore?keyword=${work}+&country=ID&locationId=${location_id}&locationName=${location_name}&lowestLocationLevel=1&jobTypes=${job_type}&workArrangementOptions=${option_work}&page=${page}`;

  try {
    const html = await ScraperHelper.get(url, "src/config/glints.json");
    const $ = cheerio.load(html);

    const results: Job[] = [];
    const seenJobs = new Set<string>();

    // Debug: Log HTML structure
    console.log("HTML Structure for debugging:");
    console.log($.html().substring(0, 2000));

    // Find job cards with multiple selectors
    let jobCards = $('div[role="presentation"][aria-label="Job Card"]');

    // Selector 2: Alternative with class pattern
    if (jobCards.length === 0) {
      jobCards = $('div[class*="JobCard"]');
    }

    console.log(`Found ${jobCards.length} job cards`);

    jobCards.each((_, element) => {
      const $card = $(element);

      // Extract title with multiple selectors
      let title = "N/A";
      let $titleTag = $card.find("h2");
      if ($titleTag.length === 0) {
        $titleTag = $card.find("h3");
      }
      if ($titleTag.length === 0) {
        $titleTag = $card.find('a[href*="/opportunities/jobs/"]');
      }
      if ($titleTag.length > 0) {
        title = $titleTag.text().trim();
      }

      // Extract salary with pattern matching
      let salary = "N/A";
      // Find spans that might contain salary
      $card.find("span").each((_, span) => {
        const $span = $(span);
        const className = $span.attr("class") || "";
        const text = $span.text();

        // Check if class contains 'Salary' or 'salary'
        if (
          className.toLowerCase().includes("salary") ||
          text.match(/Rp|IDR|\$/i)
        ) {
          salary = text.trim();
          return false; // break
        }
      });

      // If not found, search text for salary pattern
      if (salary === "N/A") {
        const cardText = $card.text();
        const salaryMatch = cardText.match(
          /Rp[\d,.\s]+|IDR[\d,.\s]+|\$[\d,.\s]+/,
        );
        if (salaryMatch) {
          salary = salaryMatch[0];
        }
      }

      // Extract location
      let location = "N/A";
      $card.find("span").each((_, span) => {
        const $span = $(span);
        const className = $span.attr("class") || "";
        const titleAttr = $span.attr("title");

        // Check if class contains 'Location' or 'location'
        if (className.toLowerCase().includes("location")) {
          location = titleAttr || $span.text().trim();
          return false; // break
        }

        // Also check for span with title attribute
        if (titleAttr && location === "N/A") {
          location = titleAttr;
        }
      });

      // Extract link
      let link = "N/A";
      const $linkTag = $card.find('a[href*="/opportunities/jobs/"]');
      if ($linkTag.length > 0) {
        const href = $linkTag.attr("href");
        if (href) {
          link = href.startsWith("/") ? `https://glints.com${href}` : href;
        }
      }

      // Extract company name
      let companyName = "N/A";
      // Try finding by class pattern
      $card.find("a").each((_, anchor) => {
        const $anchor = $(anchor);
        const className = $anchor.attr("class") || "";
        const href = $anchor.attr("href") || "";

        if (
          className.toLowerCase().includes("company") ||
          href.includes("/companies/")
        ) {
          companyName = $anchor.text().trim();
          return false; // break
        }
      });

      // Extract company logo
      let companyLogo = "N/A";
      const $logo = $card.find("img");
      if ($logo.length > 0) {
        companyLogo = $logo.attr("src") || "N/A";
      }

      // Create unique key
      const uniqueKey =
        link !== "N/A" && link.startsWith("https://glints.com")
          ? link
          : `${title.toLowerCase()}|${companyName.toLowerCase()}|${location.toLowerCase()}`;

      // Add if not duplicate and has valid data
      if (
        (title !== "N/A" || companyName !== "N/A") &&
        !seenJobs.has(uniqueKey)
      ) {
        seenJobs.add(uniqueKey);
        results.push({
          title,
          salary,
          location,
          company_name: companyName,
          company_logo: companyLogo,
          link,
        });
      }
    });

    console.log(
      `Successfully scraped ${results.length} unique jobs (removed duplicates)`,
    );

    return ResponseHelper.success(res, "Success find job", {
      jobs: results,
      total_jobs: results.length,
    });
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    console.error("Error in scraping:", errorMessage);
    return ResponseHelper.failure(res, `Error: ${errorMessage}`);
  }
};
