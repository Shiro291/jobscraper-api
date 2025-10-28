export interface ApiResponse<T = any> {
  status: "success" | "failed";
  message: string;
  data?: T;
}

export interface Job {
  title: string;
  salary: string;
  location: string;
  company_name: string;
  company_logo: string;
  link: string;
}

export interface JobsResponse {
  total_jobs?: string | number;
  jobs: Job[];
  pagination?: {
    current_page: number;
    last_page: number;
    has_next: boolean;
  };
  suggestion_location?: Array<{
    location_name: string;
    url: string;
  }>;
}

export interface Cookie {
  name: string;
  value: string;
  domain?: string;
  path?: string;
  secure?: boolean;
  httpOnly?: boolean;
  sameSite?: "Strict" | "Lax" | "None";
}

export interface GlintsParams {
  work?: string;
  job_type?: string;
  option_work?: string;
  location_id?: string;
  location_name?: string;
  page?: string;
}

export interface JobStreetParams {
  work?: string;
  location?: string;
  country?: string;
  page?: string;
}

export interface RemoteOKParams {
  keywords?: string;
  page?: string;
}

export interface IndeedParams {
  keyword?: string;
  location?: string;
  country?: string;
  page?: string;
}

export interface DisnakerParams {
  page?: string;
}

export interface DevJobsScannerParams {
  keywords?: string;
  page?: string;
}
