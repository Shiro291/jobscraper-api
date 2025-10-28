import { Request, Response } from "express";
import { ResponseHelper } from "../helpers/response.helper";
import { ScraperHelper } from "../helpers/scraper.helper";

interface DevJobsScannerParams {
  keywords?: string;
  page?: string;
}

interface DevJobsScannerJob {
  title: string;
  salary: string;
  location: string;
  company_name: string;
  company_logo: string;
  link: string;
}

interface DevJobsScannerAPIResponse {
  jobs: any[];
  [key: string]: any;
}

export const scrapeDevJobsScanner = async (
  req: Request,
  res: Response,
): Promise<Response> => {
  const { keywords = "web developer", page = "1" } =
    req.query as DevJobsScannerParams;

  // Validate page parameter
  const pageNum = parseInt(page);
  if (isNaN(pageNum) || pageNum <= 0) {
    return ResponseHelper.failure(res, "Page must be a positive integer.", 400);
  }

  const baseUrl = `https://www.devjobsscanner.com/api/searchFull/?search=${keywords}&page=${page}&db=prod`;

  try {
    // Get instance from ScraperHelper
    const response = await ScraperHelper.getInstance().get(baseUrl);

    // Parse JSON response
    const data: DevJobsScannerAPIResponse = response.data;

    // Extract jobs from response
    const jobsRaw = data.jobs || [];

    if (!jobsRaw || jobsRaw.length === 0) {
      return ResponseHelper.success(res, "No jobs found", {
        jobs: [],
        total_jobs: 0,
      });
    }

    const results: DevJobsScannerJob[] = [];
    const seenJobs = new Set<string>();

    for (const job of jobsRaw) {
      if (!job) continue;

      // Extract data from job
      const title = job.title || "N/A";
      const companyName = job.company || "N/A";
      const location = job.location || "N/A";

      // Format salary from salaryMin and salaryMax
      let salary = "N/A";
      const salaryMin = job.salaryMin || -1;
      const salaryMax = job.salaryMax || -1;
      const salaryCurrency = job.salaryCurrency || "";

      if (salaryMin > 0 && salaryMax > 0) {
        if (salaryCurrency) {
          salary = `${salaryCurrency} ${salaryMin.toLocaleString()} - ${salaryMax.toLocaleString()}`;
        } else {
          salary = `$${salaryMin.toLocaleString()} - $${salaryMax.toLocaleString()}`;
        }
      } else if (salaryMin > 0) {
        if (salaryCurrency) {
          salary = `${salaryCurrency} ${salaryMin.toLocaleString()}`;
        } else {
          salary = `$${salaryMin.toLocaleString()}`;
        }
      }

      // Extract company logo
      const companyLogo = job.img || "N/A";

      // Extract job URL
      const link = job.url || "N/A";

      // Create unique identifier to detect duplicates
      // Use job ID if available, or combination of title + company + location
      const jobId = job.id || "";
      let uniqueKey: string;

      if (jobId) {
        uniqueKey = jobId;
      } else {
        uniqueKey = `${title.toLowerCase().trim()}|${companyName.toLowerCase().trim()}|${location.toLowerCase().trim()}`;
      }

      // Alternative: Use link as unique identifier if available
      if (link !== "N/A" && link.startsWith("http")) {
        uniqueKey = link;
      }

      // Only add if not duplicate and at least title and company exist
      if (
        (title !== "N/A" || companyName !== "N/A") &&
        !seenJobs.has(uniqueKey)
      ) {
        seenJobs.add(uniqueKey);

        // Format according to standard structure
        results.push({
          title,
          salary,
          location,
          company_name: companyName,
          company_logo: companyLogo,
          link,
        });
      }
    }

    console.log(
      `Successfully scraped ${results.length} unique jobs from DevJobsScanner (removed duplicates)`,
    );

    // Return with same format as other controllers
    return ResponseHelper.success(res, "Success find job", {
      jobs: results,
      total_jobs: results.length,
    });
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    console.error("Error in scraping DevJobsScanner:", errorMessage);

    if (error instanceof SyntaxError) {
      return ResponseHelper.failure(
        res,
        `Failed to parse response: ${errorMessage}`,
      );
    }

    return ResponseHelper.failure(res, `Error: ${errorMessage}`);
  }
};
