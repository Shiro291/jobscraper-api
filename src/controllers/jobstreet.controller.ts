import { Request, Response } from "express";
import * as cheerio from "cheerio";
import { ResponseHelper } from "../helpers/response.helper";
import { ScraperHelper } from "../helpers/scraper.helper";
import { JobStreetParams, Job } from "../types";

export class JobStreetController {
  private static readonly COUNTRY_URLS: Record<string, string> = {
    id: "https://id.jobstreet.com/id/{work}-jobs/in-{location}?page={page}",
    my: "https://my.jobstreet.com/{work}-jobs/in-{location}?page={page}",
    sg: "https://sg.jobstreet.com/{work}-jobs/in-{location}?page={page}",
    th: "https://th.jobsdb.com/th/{work}-jobs/in-{location}?page={page}",
    hk: "https://hk.jobsdb.com/{work}-jobs/in-{location}?page={page}",
    nz: "https://www.seek.co.nz/{work}-jobs/in-{location}?page={page}",
    au: "https://www.seek.com.au/{work}-jobs/in-{location}?page={page}",
  };

  static async scrapeJobStreet(req: Request, res: Response): Promise<Response> {
    const {
      work = "Programmer",
      location = "",
      country = "id",
      page = "1",
    } = req.query as JobStreetParams;

    const countryCode = country.toLowerCase();
    if (!this.COUNTRY_URLS[countryCode]) {
      return ResponseHelper.failure(
        res,
        `Invalid country code: ${country}`,
        400,
      );
    }

    const pageNum = parseInt(page);
    if (isNaN(pageNum) || pageNum < 1) {
      return ResponseHelper.failure(
        res,
        "Page must be a positive integer",
        400,
      );
    }

    const urlTemplate = this.COUNTRY_URLS[countryCode];
    const url = urlTemplate
      .replace("{work}", work)
      .replace("{location}", location)
      .replace("{page}", page);

    try {
      const html = await ScraperHelper.get(url);
      const $ = cheerio.load(html);

      // Get total jobs
      const $totalJobs = $(
        '#SearchSummary[data-automation="totalJobsMessage"]',
      );
      const totalJobs =
        $totalJobs.find('[data-automation="totalJobsCount"]').text().trim() ||
        "0";

      // Get job cards
      const jobCards = $('article[data-automation="normalJob"]');
      const results: Job[] = [];

      jobCards.each((_, element) => {
        const $card = $(element);

        // Extract title
        const $title = $card.find('a[data-automation="jobTitle"]');
        const title = $title.text().trim() || "N/A";

        // Extract company name
        const $company = $card.find('a[data-automation="jobCompany"]');
        const companyName = $company.text().trim() || "N/A";

        // Extract company logo
        const $logoContainer = $card.find(
          'div[data-automation="company-logo-container"]',
        );
        const $logo = $logoContainer.find("img");
        const companyLogo = $logo.attr("src") || "N/A";

        // Extract salary
        const $salary = $card.find('span[data-automation="jobSalary"]');
        const salary = $salary.text().trim() || "N/A";

        // Extract location
        const $locations = $card.find('a[data-automation="jobLocation"]');
        const locationParts: string[] = [];
        $locations.each((_, loc) => {
          locationParts.push($(loc).text().trim());
        });
        const jobLocation = locationParts.join(", ") || "N/A";

        // Extract link
        const href = $title.attr("href");
        const domain = new URL(url).hostname;
        const link = href ? `https://${domain}${href}` : "N/A";

        results.push({
          title,
          company_name: companyName,
          company_logo: companyLogo,
          salary,
          location: jobLocation,
          link,
        });
      });

      // Parse pagination
      const $pagination = $("ul._1ungv2r0._1ungv2r3._1viagsn5b._1viagsngv");
      let lastPage = 1;
      let hasNext = false;

      if ($pagination.length) {
        // Find all page numbers
        const $pageLinks = $pagination.find('a[data-automation*="page-"]');
        const pageNumbers: number[] = [];

        $pageLinks.each((_, el) => {
          const pageText = $(el).text().trim();
          const num = parseInt(pageText);
          if (!isNaN(num)) {
            pageNumbers.push(num);
          }
        });

        if (pageNumbers.length > 0) {
          lastPage = Math.max(...pageNumbers);
        }

        // Check for next button
        const $nextButton = $pagination.find('a[rel="nofollow next"]');
        hasNext = $nextButton.length > 0;
      }

      // Parse suggestion locations
      const $suggestionSpan = $("span._1ungv2r0._1viagsn4z._1viagsnr");
      const suggestionLocation: Array<{ location_name: string; url: string }> =
        [];

      if ($suggestionSpan.length) {
        const $suggestionLinks = $suggestionSpan.find(
          'a[data-automation*="didYouMeanLocation"]',
        );
        $suggestionLinks.each((_, el) => {
          const $link = $(el);
          const locationName = $link.text().trim();
          const href = $link.attr("href");
          const domain = new URL(url).hostname;
          const suggestionUrl = href ? `https://${domain}${href}` : "N/A";

          suggestionLocation.push({
            location_name: locationName,
            url: suggestionUrl,
          });
        });
      }

      return ResponseHelper.success(res, "Success find job", {
        total_jobs: totalJobs,
        jobs: results,
        pagination: {
          current_page: pageNum,
          last_page: lastPage,
          has_next: hasNext,
        },
        suggestion_location: suggestionLocation,
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      return ResponseHelper.failure(res, `Error: ${errorMessage}`);
    }
  }
}
