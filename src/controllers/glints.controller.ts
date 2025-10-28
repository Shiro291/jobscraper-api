import { Request, Response } from "express";
import * as cheerio from "cheerio";
import { ResponseHelper } from "../helpers/response.helper";
import { ScraperHelper } from "../helpers/scraper.helper";
import { GlintsParams, Job } from "../types";

export class GlintsController {
  private static readonly VALID_JOB_TYPES = [
    "FULL_TIME",
    "PART_TIME",
    "CONTRACT",
    "INTERNSHIP",
  ];
  private static readonly VALID_WORK_OPTIONS = ["ONSITE", "HYBRID", "REMOTE"];
  private static readonly VALID_LOCATION_NAMES = [
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
  private static readonly VALID_LOCATION_IDS = [
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

  static async scrapeGlints(req: Request, res: Response): Promise<Response> {
    const {
      work = "Programmer",
      job_type = "FULL_TIME",
      option_work = "ONSITE",
      location_id = "",
      location_name = "All+Cities/Provinces",
      page = "1",
    } = req.query as GlintsParams;

    // Validasi parameter
    if (!this.VALID_JOB_TYPES.includes(job_type)) {
      return ResponseHelper.failure(
        res,
        `Invalid job_type: ${job_type}. Valid options: ${this.VALID_JOB_TYPES.join(", ")}`,
        400,
      );
    }

    if (!this.VALID_WORK_OPTIONS.includes(option_work)) {
      return ResponseHelper.failure(
        res,
        `Invalid option_work: ${option_work}. Valid options: ${this.VALID_WORK_OPTIONS.join(", ")}`,
        400,
      );
    }

    if (!this.VALID_LOCATION_IDS.includes(location_id)) {
      return ResponseHelper.failure(
        res,
        `Invalid location_id: ${location_id}`,
        400,
      );
    }

    if (!this.VALID_LOCATION_NAMES.includes(location_name)) {
      return ResponseHelper.failure(
        res,
        `Invalid location_name: ${location_name}`,
        400,
      );
    }

    const pageNum = parseInt(page);
    if (isNaN(pageNum) || pageNum <= 0) {
      return ResponseHelper.failure(
        res,
        "Page must be a positive integer",
        400,
      );
    }

    const url = `https://glints.com/id/opportunities/jobs/explore?keyword=${work}&country=ID&locationId=${location_id}&locationName=${location_name}&lowestLocationLevel=1&jobTypes=${job_type}&workArrangementOptions=${option_work}&page=${page}`;

    try {
      const html = await ScraperHelper.get(url, "src/config/glints.json");
      const $ = cheerio.load(html);

      const results: Job[] = [];
      const seenJobs = new Set<string>();

      // Find job cards dengan berbagai selector
      const jobCards = $('div[role="presentation"][aria-label="Job Card"]');

      jobCards.each((_, element) => {
        const $card = $(element);

        // Extract title
        let title = "N/A";
        const $titleH2 = $card.find("h2");
        const $titleH3 = $card.find("h3");
        const $titleLink = $card.find('a[href*="/opportunities/jobs/"]');

        if ($titleH2.length) {
          title = $titleH2.text().trim();
        } else if ($titleH3.length) {
          title = $titleH3.text().trim();
        } else if ($titleLink.length) {
          title = $titleLink.text().trim();
        }

        // Extract salary
        let salary = "N/A";
        const $salary = $card.find('span[class*="Salary" i]');
        if ($salary.length) {
          salary = $salary.text().trim();
        }

        // Extract location
        let location = "N/A";
        const $location = $card.find('span[class*="Location" i]');
        if ($location.length) {
          location = $location.attr("title") || $location.text().trim();
        }

        // Extract link
        let link = "N/A";
        if ($titleLink.length) {
          const href = $titleLink.attr("href");
          if (href) {
            link = href.startsWith("/") ? `https://glints.com${href}` : href;
          }
        }

        // Extract company name
        let companyName = "N/A";
        const $company = $card.find(
          'a[class*="Company" i], a[href*="/companies/"]',
        );
        if ($company.length) {
          companyName = $company.text().trim();
        }

        // Extract company logo
        let companyLogo = "N/A";
        const $logo = $card.find("img");
        if ($logo.length) {
          companyLogo = $logo.attr("src") || "N/A";
        }

        // Create unique key
        const uniqueKey =
          link !== "N/A" && link.startsWith("https://glints.com")
            ? link
            : `${title.toLowerCase()}|${companyName.toLowerCase()}|${location.toLowerCase()}`;

        // Add if not duplicate
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

      return ResponseHelper.success(res, "Success find job", {
        jobs: results,
        total_jobs: results.length,
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      return ResponseHelper.failure(res, `Error: ${errorMessage}`);
    }
  }
}
