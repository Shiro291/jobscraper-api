import { Request, Response } from "express";
import * as cheerio from "cheerio";
import { ResponseHelper } from "../helpers/response.helper";
import { ScraperHelper } from "../helpers/scraper.helper";

interface DisnakerParams {
  page?: string;
}

interface DisnakerJob {
  company_logo: string;
  company_name: string;
  title: string;
  location: string;
  salary: string;
  link: string;
}

interface DisnakerResponse {
  jobs: DisnakerJob[];
  total_results: number;
  showing_start: number;
  showing_end: number;
  total_pages: number;
  current_page: number;
  is_last_page: boolean;
}

export const scrapeDisnakerBandung = async (
  req: Request,
  res: Response,
): Promise<Response> => {
  const { page = "1" } = req.query as DisnakerParams;

  const pageNum = parseInt(page);
  if (isNaN(pageNum) || pageNum < 1) {
    return ResponseHelper.failure(res, "Page must be a positive integer", 400);
  }

  const url = `https://disnaker.bandung.go.id/loker?page=${page}`;

  try {
    const html = await ScraperHelper.get(url);
    const $ = cheerio.load(html);

    // Get all job elements
    const jobElements = $("div.col-sm-3.loker");
    const results: DisnakerJob[] = [];

    jobElements.each((_, job) => {
      const $job = $(job);

      // Extract logo
      const $logoTag = $job.find("img");
      const logo = $logoTag.attr("src") || "N/A";

      // Extract company name
      const $companyTag = $job.find('p[style*="font-size:13px"]');
      const company = $companyTag.text().trim() || "N/A";

      // Extract job title
      const $titleTag = $job.find("b");
      const title = $titleTag.text().trim() || "N/A";

      // Extract location
      const $locationTag = $job.find('p[style*="font-size:10px"]');
      const location =
        $locationTag.text().trim().replace(/\n/g, "").replace(/\r/g, "") ||
        "N/A";

      // Extract detail link
      const $linkTag = $job.find("a.btn.btn-sm.btn-danger");
      const link = $linkTag.attr("href") || "N/A";

      // Add to results only if not all fields are empty
      if (
        !(
          logo === "N/A" &&
          company === "N/A" &&
          title === "N/A" &&
          location === "N/A"
        )
      ) {
        results.push({
          company_logo: logo,
          company_name: company,
          title,
          location,
          salary: "Klik open untuk info gaji",
          link,
        });
      }
    });

    // Extract total results and "showing" information
    const $totalResultTag = $("p.small.text-muted");
    let totalResults = 0;
    let showingStart = 0;
    let showingEnd = 0;

    if ($totalResultTag.length) {
      const resultText = $totalResultTag.html() || "";
      const match = resultText.match(
        /Showing\s+<span class="fw-semibold">(\d+)<\/span>\s+to\s+<span class="fw-semibold">(\d+)<\/span>\s+of\s+<span class="fw-semibold">(\d+)<\/span>/,
      );

      if (match) {
        showingStart = parseInt(match[1]);
        showingEnd = parseInt(match[2]);
        totalResults = parseInt(match[3]);
      }
    }

    // Extract pagination
    const $paginationTag = $("ul.pagination");
    let totalPages = 0;

    if ($paginationTag.length) {
      const $pageItems = $paginationTag.find("a.page-link");
      const pageNumbers: number[] = [];

      $pageItems.each((_, item) => {
        const pageText = $(item).text().trim();
        if (/^\d+$/.test(pageText)) {
          pageNumbers.push(parseInt(pageText));
        }
      });

      totalPages = pageNumbers.length > 0 ? Math.max(...pageNumbers) : 0;
    }

    // Validate if page has ended
    if (
      showingStart === 0 &&
      showingEnd === 0 &&
      totalPages === 0 &&
      totalResults === 0
    ) {
      return ResponseHelper.success(res, "No more data available.", {
        jobs: [],
        total_results: 0,
        showing_start: 0,
        showing_end: 0,
        total_pages: 0,
        current_page: pageNum,
        is_last_page: true,
      });
    }

    const responseData: DisnakerResponse = {
      jobs: results,
      total_results: totalResults,
      showing_start: showingStart,
      showing_end: showingEnd,
      total_pages: totalPages,
      current_page: pageNum,
      is_last_page: showingEnd === totalResults,
    };

    return ResponseHelper.success(
      res,
      "Success scraping Disnaker Bandung jobs",
      responseData,
    );
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    return ResponseHelper.failure(res, `Error: ${errorMessage}`);
  }
};
