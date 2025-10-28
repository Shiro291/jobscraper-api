import { Response } from "express";
import { ApiResponse } from "../types";

export class ResponseHelper {
  /**
   * Send success response
   */
  static success<T>(
    res: Response,
    message: string,
    data: T,
    statusCode: number = 200,
  ): Response {
    const response: ApiResponse<T> = {
      status: "success",
      message,
      data,
    };
    return res.status(statusCode).json(response);
  }

  /**
   * Send failure response
   */
  static failure(
    res: Response,
    message: string,
    statusCode: number = 500,
  ): Response {
    const response: ApiResponse = { status: "failed", message };
    return res.status(statusCode).json(response);
  }
}
