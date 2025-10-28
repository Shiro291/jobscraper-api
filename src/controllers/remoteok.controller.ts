import { Request, Response } from "express";
import * as cheerio from "cheerio";
import { ResponseHelper } from "../helpers/response.helper";
import { ScraperHelper } from "../helpers/scraper.helper";

interface RemoteOKParams {
  keywords?: string;
  page?: string;
}

interface RemoteOKJob {
  title: string;
  company_name: string;
  location: string;
  salary: string;
  company_logo: string;
  link: string;
}

export const scrapeRemoteOK = async (
  req: Request,
  res: Response,
): Promise<Response> => {
  const { keywords = "engineer", page = "1" } = req.query as RemoteOKParams;

  const pageNum = parseInt(page);
  if (isNaN(pageNum) || pageNum < 1) {
    return ResponseHelper.failure(res, "Page must be a positive integer", 400);
  }

  // Calculate offset: page 1 = 0, page 2 = 10, page 3 = 20, etc
  const offset = (pageNum - 1) * 10;

  const baseUrl = `https://remoteok.com/?location=Worldwide&tags=${keywords}&action=get_jobs&premium=0&offset=${offset}`;

  try {
    const html = await ScraperHelper.get(baseUrl);
    const $ = cheerio.load(html);

    // Get all script JSON-LD that contains job data
    const jsonLdScripts = $('script[type="application/ld+json"]');
    const results: RemoteOKJob[] = [];

    jsonLdScripts.each((_, script) => {
      try {
        const scriptContent = $(script).html();
        if (!scriptContent) return;

        // Parse JSON data
        const jobData = JSON.parse(scriptContent);

        // Ensure this is a JobPosting schema
        if (jobData["@type"] !== "JobPosting") {
          return;
        }

        // Extract data from JSON-LD
        const title = jobData.title || "N/A";

        // Company name and logo from hiringOrganization
        const hiringOrg = jobData.hiringOrganization || {};
        const companyName = hiringOrg.name || "N/A";

        // Logo can be from image or hiringOrganization.logo.url
        let logoUrl = jobData.image;
        if (!logoUrl && hiringOrg.logo) {
          logoUrl = hiringOrg.logo.url || hiringOrg.logo;
        }
        if (!logoUrl) {
          logoUrl = "N/A";
        }

        // Extract salary
        let salaryText = "N/A";
        const baseSalary = jobData.baseSalary;
        if (baseSalary && typeof baseSalary === "object") {
          const salaryValue = baseSalary.value || {};
          if (typeof salaryValue === "object") {
            const minVal = salaryValue.minValue;
            const maxVal = salaryValue.maxValue;
            const currency = baseSalary.currency || "USD";

            if (minVal && maxVal) {
              // Format salary like: $60k - $120k
              const minK = Math.floor(minVal / 1000);
              const maxK = Math.floor(maxVal / 1000);
              salaryText = `💰 $${minK}k - $${maxK}k`;
            }
          }
        }

        // Extract location
        let locationText = "🌏 Worldwide";
        const applicantReqs = jobData.applicantLocationRequirements || [];
        if (applicantReqs.length > 0) {
          const locationName = applicantReqs[0].name || "Worldwide";
          if (locationName === "Anywhere") {
            locationText = "🌏 Worldwide";
          } else {
            locationText = `🌏 ${locationName}`;
          }
        }

        // Find job link - search for next anchor element after script
        let jobLink = "N/A";
        const scriptElement = $(script);
        const nextAnchor = scriptElement.next("a");

        if (nextAnchor.length && nextAnchor.attr("href")) {
          const href = nextAnchor.attr("href")!;
          if (href.includes("/remote-jobs/")) {
            jobLink = `https://remoteok.com${href}`;
          }
        }

        // If not found, try finding next sibling anchor
        if (jobLink === "N/A") {
          let currentElement = scriptElement;
          for (let i = 0; i < 5; i++) {
            currentElement = currentElement.next();
            if (currentElement.is("a") && currentElement.attr("href")) {
              const href = currentElement.attr("href")!;
              if (href.includes("/remote-jobs/")) {
                jobLink = `https://remoteok.com${href}`;
                break;
              }
            }
          }
        }

        // Add to results
        results.push({
          title,
          company_name: companyName,
          location: locationText,
          salary: salaryText,
          company_logo: logoUrl,
          link: jobLink,
        });
      } catch (e) {
        // Skip jobs that fail to parse
        return;
      }
    });

    return ResponseHelper.success(res, "Success scraping RemoteOK jobs", {
      jobs: results,
      pagination: {
        current_page: pageNum,
      },
    });
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    return ResponseHelper.failure(res, `Error: ${errorMessage}`);
  }
};
