import fs from "fs";
import path from "path";
import { Cookie } from "../types";

export class CookieHelper {
  /**
   * Load cookies from JSON file
   */
  static loadCookies(filePath: string): string {
    try {
      const absolutePath = path.resolve(filePath);

      if (!fs.existsSync(absolutePath)) {
        throw new Error(`Cookie file not found: ${filePath}`);
      }

      const cookiesData = fs.readFileSync(absolutePath, "utf-8");
      const cookies: Cookie[] = JSON.parse(cookiesData);

      // Convert cookies array to cookie string
      const cookieString = cookies
        .map((cookie) => `${cookie.name}=${cookie.value}`)
        .join("; ");

      return cookieString;
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(
          `Failed to load cookies from ${filePath}: ${error.message}`,
        );
      }
      throw error;
    }
  }
}
