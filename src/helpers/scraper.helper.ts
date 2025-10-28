import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import { CookieHelper } from "./cookie.helper";

export class ScraperHelper {
  private static instance: AxiosInstance | null = null;

  /**
   * Get or create axios instance with anti-bot measures
   */
  static getInstance(cookiesFile?: string): AxiosInstance {
    if (!this.instance) {
      this.instance = axios.create({
        timeout: 30000,
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
          Accept:
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
          "Accept-Encoding": "gzip, deflate, br",
          Connection: "keep-alive",
          "Upgrade-Insecure-Requests": "1",
          "Sec-Fetch-Dest": "document",
          "Sec-Fetch-Mode": "navigate",
          "Sec-Fetch-Site": "none",
        },
      });
    }

    return this.instance;
  }

  /**
   * Make a GET request with cookies
   */
  static async get(url: string, cookiesFile?: string): Promise<string> {
    const instance = this.getInstance(cookiesFile);
    const config: AxiosRequestConfig = {};

    if (cookiesFile) {
      const cookieString = CookieHelper.loadCookies(cookiesFile);
      config.headers = { ...config.headers, Cookie: cookieString };
    }

    const response = await instance.get(url, config);
    return response.data;
  }
}
