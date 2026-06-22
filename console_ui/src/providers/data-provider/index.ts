"use client";

import dataProviderSimpleRest from "@refinedev/simple-rest";
import axiosInstance from "./axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

const dataProvider = dataProviderSimpleRest(API_URL, axiosInstance);

export default dataProvider;
