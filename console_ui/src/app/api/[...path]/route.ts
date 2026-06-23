import { NextRequest } from "next/server";

const HOP_BY_HOP_HEADERS = [
	"connection",
	"content-encoding",
	"content-length",
	"host",
	"keep-alive",
	"proxy-authenticate",
	"proxy-authorization",
	"te",
	"trailer",
	"transfer-encoding",
	"upgrade",
] as const;

type RouteContext = {
	params: {
		path?: string[];
	};
};

function buildTargetUrl(request: NextRequest, path: string[] = []) {
	const upstreamBaseUrl = process.env.PHOENIX_INTERNAL_API_URL;
	if (!upstreamBaseUrl) {
		return null;
	}

	const targetUrl = new URL(
		path.join("/"),
		ensureTrailingSlash(upstreamBaseUrl)
	);
	targetUrl.search = request.nextUrl.search;
	return targetUrl;
}

function ensureTrailingSlash(value: string) {
	return value.endsWith("/") ? value : `${value}/`;
}

function buildRequestHeaders(request: NextRequest) {
	const headers = new Headers(request.headers);
	for (const headerName of HOP_BY_HOP_HEADERS) {
		headers.delete(headerName);
	}
	headers.set("x-forwarded-host", request.headers.get("host") ?? "");
	headers.set("x-forwarded-proto", request.nextUrl.protocol.replace(":", ""));
	return headers;
}

function buildResponseHeaders(upstreamHeaders: Headers) {
	const headers = new Headers(upstreamHeaders);
	for (const headerName of HOP_BY_HOP_HEADERS) {
		headers.delete(headerName);
	}
	return headers;
}

async function proxyRequest(request: NextRequest, context: RouteContext) {
	const targetUrl = buildTargetUrl(request, context.params.path);
	if (!targetUrl) {
		return Response.json(
			{ message: "PHOENIX_INTERNAL_API_URL is not configured" },
			{ status: 503 }
		);
	}

	const requestBody =
		request.method === "GET" || request.method === "HEAD"
			? undefined
			: Buffer.from(await request.arrayBuffer());

	const proxyFetch = async (url: URL) =>
		fetch(url, {
			body: requestBody,
			headers: buildRequestHeaders(request),
			method: request.method,
			redirect: "manual",
		});

	let upstreamResponse = await proxyFetch(targetUrl);
	const redirectLocation = upstreamResponse.headers.get("location");
	if (
		(redirectLocation?.length ?? 0) > 0 &&
		(upstreamResponse.status === 307 || upstreamResponse.status === 308)
	) {
		upstreamResponse = await proxyFetch(new URL(redirectLocation!, targetUrl));
	}

	return new Response(upstreamResponse.body, {
		headers: buildResponseHeaders(upstreamResponse.headers),
		status: upstreamResponse.status,
		statusText: upstreamResponse.statusText,
	});
}

export async function GET(request: NextRequest, context: RouteContext) {
	return proxyRequest(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
	return proxyRequest(request, context);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
	return proxyRequest(request, context);
}

export async function PUT(request: NextRequest, context: RouteContext) {
	return proxyRequest(request, context);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
	return proxyRequest(request, context);
}

export async function OPTIONS(request: NextRequest, context: RouteContext) {
	return proxyRequest(request, context);
}
