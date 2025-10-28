import { Request, Response } from "express";
import * as cheerio from "cheerio";
import { ResponseHelper } from "../helpers/response.helper";
import { ScraperHelper } from "../helpers/scraper.helper";

interface IndeedParams {
  keyword?: string;
  location?: string;
  country?: string;
  page?: string;
}

interface IndeedJob {
  title: string;
  company: string;
  location: string;
  sallary: string;
  link: string;
}

const COUNTRY_URLS: Record<string, string> = {
  id: "https://id.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  nl: "https://nl.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  sa: "https://sa.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  jp: "https://jp.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  cn: "https://cn.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  fr: "https://fr.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  de: "https://de.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  ar: "https://ar.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  ca: "https://ca.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  pt: "https://pt.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  co: "https://co.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  mx: "https://mx.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  my: "https://my.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  tw: "https://tw.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  in: "https://in.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  uk: "https://uk.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  ru: "https://ru.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  es: "https://es.indeed.com/jobs?q={keyword}&l={location}{page_param}",
  it: "https://it.indeed.com/jobs?q={keyword}&l={location}{page_param}",
};

export const scrapeIndeed = async (
  req: Request,
  res: Response,
): Promise<Response> => {
  const {
    keyword = "programmer",
    location = "",
    country = "id",
    page = "",
  } = req.query as IndeedParams;

  const countryCode = country.toLowerCase();
  if (!COUNTRY_URLS[countryCode]) {
    return ResponseHelper.failure(
      res,
      `Invalid country code: ${country}. Valid options: ${Object.keys(COUNTRY_URLS).join(", ")}`,
      400,
    );
  }

  // Determine page parameter only if page is not empty
  const pageParam = page ? `&start=${page}` : "";

  // Build URL
  const urlTemplate = COUNTRY_URLS[countryCode];
  const url = urlTemplate
    .replace("{keyword}", keyword)
    .replace("{location}", location)
    .replace("{page_param}", pageParam);

  try {
    const html = await ScraperHelper.get(url, "src/config/indeed.json");
    const $ = cheerio.load(html);

    // Get all job listings
    const jobListings = $("li.css-1ac2h1w.eu4oa1w0");
    const results: IndeedJob[] = [];

    jobListings.each((_, job) => {
      const $job = $(job);

      // Extract Title
      const $titleTag = $job.find("h2.jobTitle");
      const title = $titleTag.text().trim() || "N/A";

      // Extract Company Name
      const $companyTag = $job.find('span[data-testid="company-name"]');
      const company = $companyTag.text().trim() || "N/A";

      // Extract Location
      const $locationTag = $job.find('div[data-testid="text-location"]');
      const jobLocation = $locationTag.text().trim() || "N/A";

      // Extract Short Description (salary info usually in ul)
      const $descriptionTag = $job.find("ul");
      const description = $descriptionTag.text().trim() || "N/A";

      // Extract Job Link
      const $linkTag = $job.find("a.jcs-JobTitle");
      let link = "N/A";
      if ($linkTag.length && $linkTag.attr("href")) {
        const href = $linkTag.attr("href")!;
        link = `https://${countryCode}.indeed.com${href}`;
      }

      // Add to results only if not all fields are N/A
      if (
        !(
          title === "N/A" &&
          company === "N/A" &&
          jobLocation === "N/A" &&
          description === "N/A"
        )
      ) {
        results.push({
          title,
          company,
          location: jobLocation,
          sallary: description,
          link,
        });
      }
    });

    // Extract Pagination
    const $pagination = $("ul.css-1g90gv6.eu4oa1w0");
    let lastPage = 1;

    if ($pagination.length) {
      const $pageLinks = $pagination.find("a");
      const lastPageNumbers: number[] = [];

      $pageLinks.each((_, link) => {
        const $link = $(link);
        const dataTestId = $link.attr("data-testid");
        const ariaLabel = $link.attr("aria-label");

        // Check if data-testid matches pagination-page-\d+
        if (dataTestId && /pagination-page-\d+/.test(dataTestId)) {
          if (ariaLabel) {
            const pageNum = parseInt(ariaLabel);
            if (!isNaN(pageNum)) {
              lastPageNumbers.push(pageNum);
            }
          }
        }
      });

      if (lastPageNumbers.length > 0) {
        lastPage = Math.max(...lastPageNumbers);
      }
    }

    // Use 0 if page is empty
    const currentPage = page ? parseInt(page) : 0;
    const nextPage =
      page && !isNaN(parseInt(page)) && parseInt(page) + 10 < lastPage * 10
        ? parseInt(page) + 10
        : null;

    return ResponseHelper.success(res, "Success scraping Indeed jobs", {
      jobs: results,
      pagination: {
        current_page: currentPage,
        last_page: lastPage,
        next_page: nextPage,
      },
    });
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    return ResponseHelper.failure(res, `Error: ${errorMessage}`);
  }
};
