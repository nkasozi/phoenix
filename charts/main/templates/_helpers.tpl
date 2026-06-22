{{/*
Define scheme based on cert_issuer.enabled
*/}}
{{- define "phoenixmain.scheme" -}}
{{- if .Values.cert_issuer.enabled -}}
https
{{- else -}}
http
{{- end -}}
{{- end -}}

{{/*
Generate auth-signin annotation value
*/}}
{{- define "phoenixmain.authSignin" -}}
nginx.ingress.kubernetes.io/auth-signin: {{ include "phoenixmain.scheme" . }}://oauth.{{ .Values.base_host }}/oauth2/start?rd={{ include "phoenixmain.scheme" . }}://$host$uri
{{- end -}}


{{/*
Generte the Ingress nginx cors
*/}}
{{- define "phoenixmain.ingress_cors" -}}
{{- if .Values.ingress_cors.enabled }}
nginx.ingress.kubernetes.io/enable-cors: "true"
nginx.ingress.kubernetes.io/cors-allow-origin: {{ tpl .Values.ingress_cors.allow_origin . }}
{{- end }}
{{- end -}}

{{/*
Phiphi container
*/}}
{{- define "phoenixmain.phiphi_container" -}}
image: {{ tpl (.Values.api.image.repository ) . }}:{{ tpl (.Values.api.image.tag) . }}
imagePullPolicy: {{ .Values.api.image.pullPolicy }}
ports:
  - containerPort: 80
env:
  - name: IMAGE_URI
    value: {{ tpl .Values.api.image.repository . }}:{{ tpl .Values.api.image.tag . }}
  - name: PHIPHI_LOG_CONFIG
    value: {{ .Values.api.phiphiLogConfig | quote }}
  - name: SQLALCHEMY_DATABASE_URI
    valueFrom:
      secretKeyRef:
        name: {{ tpl ( .Values.api.secretKey ) . }}
        key: SQLALCHEMY_DATABASE_URI
  - name: CORS_ORIGINS
    value: {{ tpl ( .Values.api.cors_origins ) .}}
  - name: FIRST_ADMIN_USER_EMAIL
    value: {{ .Values.api.first_admin_user_email | quote }}
  - name: FIRST_ADMIN_USER_DISPLAY_NAME
    value: {{ .Values.api.first_admin_user_display_name | quote }}
  - name: HEADER_AUTH_NAME
    value: {{ .Values.api.header_auth_name | quote}}
  # There are alot of problems with setting the forwarded allow ips when used in the cli command.
  # For instances you have to do `--forwarded-allow-ips=*` with no quotes (double or single) around the *
  - name: FORWARDED_ALLOW_IPS
    value: {{ .Values.api.forwarded_allow_ips | quote}}
  - name: USE_MOCK_APIFY
    value: {{ .Values.api.use_mock_apify | quote }}
  - name: USE_MOCK_DANEK
    value: {{ .Values.api.useMockDanek | quote }}
  - name: VERSION
    value: {{ tpl (.Values.api.version) . | quote }}
  - name: INCLUDE_INSECURE_AUTH
  {{- if .Values.use_local_insecure_auth }}
    value: "true"
  {{- else }}
    value: "false"
  {{- end }}
  {{- if .Values.gcp_service_account.enabled }}
  - name: GOOGLE_APPLICATION_CREDENTIALS
    value: /var/secrets/google/{{ .Values.gcp_service_account.secret_key }}
  {{- end }}
  {{- if .Values.api.apify_api_keys.enabled }}
  - name: APIFY_API_KEYS
    valueFrom:
      secretKeyRef:
        name: {{ tpl ( .Values.api.apify_api_keys.secret_name ) . }}
        key: {{ .Values.api.apify_api_keys.secret_key }}
  {{- end }}
  {{- if .Values.api.huggingFaceToken.enabled }}
  - name: HF_TOKEN
    valueFrom:
      secretKeyRef:
        name: {{ tpl ( .Values.api.huggingFaceToken.secretName ) . }}
        key: {{ .Values.api.huggingFaceToken.secretKey }}
  {{- end }}
  - name: HF_GCS_BUCKET_NAME
    value: {{ .Values.api.hfGcsBucketName | quote }}
  {{- if .Values.api.hfFlowName }}
  - name: HF_FLOW_NAME
    value: {{ .Values.api.hfFlowName | quote }}
  {{- end }}
  {{- if .Values.api.hfFlowTimeoutSeconds }}
  - name: HF_FLOW_TIMEOUT_SECONDS
    value: {{ .Values.api.hfFlowTimeoutSeconds | quote }}
  {{- end }}
  {{- if .Values.api.danekApiTokens.enabled }}
  - name: DANEK_API_TOKENS
    valueFrom:
      secretKeyRef:
        name: {{ tpl ( .Values.api.danekApiTokens.secretName ) . }}
        key: {{ .Values.api.danekApiTokens.secretKey }}
  {{- end }}
  {{- if and .Values.prefect .Values.prefect.apiKey }}
  - name: PREFECT_API_KEY
    valueFrom:
      secretKeyRef:
        name: prefect-api-key
        key: key
  {{- end }}
  {{- if index (index .Values "prefect-worker" ) "enabled" }}
  - name: PREFECT_API_URL
    # This uses the subchart to get the prefect-worker url
    value: {{ include "worker.apiUrl" (index  .Subcharts "prefect-worker") }}
  {{- end }}
  {{- if .Values.api.bqDefaultLocation }}
  - name: BQ_DEFAULT_LOCATION
    value: {{ .Values.api.bqDefaultLocation | quote }}
  {{- end }}
  {{- if .Values.api.prefectLoggingSettingsPath }}
  - name: PREFECT_LOGGING_SETTINGS_PATH
    value: {{ .Values.api.prefectLoggingSettingsPath | quote }}
  {{- end }}
  {{- if .Values.api.sentryDsn }}
  - name: SENTRY_DSN
    value: {{ .Values.api.sentryDsn | quote }}
  {{- end }}
  {{- if .Values.api.sentryTracesSampleRate }}
  - name: SENTRY_TRACES_SAMPLE_RATE
    value: {{ .Values.api.sentryTracesSampleRate | quote }}
  {{- end }}
  {{- if .Values.api.sentryProfilesSampleRate }}
  - name: SENTRY_PROFILES_SAMPLE_RATE
    value: {{ .Values.api.sentryProfilesSampleRate | quote }}
  {{- end }}
  {{- if .Values.api.sentryEnvironment }}
  - name: SENTRY_ENVIRONMENT
    value: {{ .Values.api.sentryEnvironment | quote }}
  {{- end }}
  {{- if .Values.api.prefectDefaultResultStorageBlock }}
  - name: PREFECT_RESULTS_PERSIST_BY_DEFAULT
    value: "true"
  - name: PREFECT_DEFAULT_RESULT_STORAGE_BLOCK
    value: {{ .Values.api.prefectDefaultResultStorageBlock | quote }}
  {{- end }}
  {{- if .Values.api.manualUploadStorageUrl }}
  - name: MANUAL_UPLOAD_STORAGE_URL
    value: {{ .Values.api.manualUploadStorageUrl | quote }}
  {{- end }}
  {{- if .Values.api.maxManualUploadFileSize }}
  - name: MAX_MANUAL_UPLOAD_FILE_SIZE
    value: {{ .Values.api.maxManualUploadFileSize | quote }}
  {{- end }}
  {{- if .Values.api.apifyTimeoutSecs }}
  - name: APIFY_TIMEOUT_SECS
    value: {{ .Values.api.apifyTimeoutSecs | quote }}
  {{- end }}
  {{- if .Values.api.apifyWaitSecs }}
  - name: APIFY_WAIT_SECS
    value: {{ .Values.api.apifyWaitSecs | quote }}
  {{- end }}
  {{- if .Values.api.innerFlowTimeoutSecs }}
  - name: INNER_FLOW_TIMEOUT_SECS
    value: {{ .Values.api.innerFlowTimeoutSecs | quote }}
  {{- end }}
  {{- if .Values.api.defaultBatchOfBatchesSize }}
  - name: DEFAULT_BATCH_OF_BATCHES_SIZE
    value: {{ .Values.api.defaultBatchOfBatchesSize | quote }}
  {{- end }}
  {{- if .Values.api.perspectiveApiKey }}
  - name: PERSPECTIVE_API_KEY
    valueFrom:
      secretKeyRef:
        name: {{ tpl ( .Values.perspectiveApiKey.secret_name ) . }}
        key: {{ .Values.perspectiveApiKey.secret_key }}
  {{- end }}
  {{- if .Values.api.perspectiveApiMaxParallelWorkers }}
  - name: PERSPECTIVE_API_MAX_PARALLEL_WORKERS
    value: {{ .Values.api.perspectiveApiMaxParallelWorkers | quote }}
  {{- end }}
  {{- if .Values.api.perspectiveApiRequestLimitForPeriod }}
  - name: PERSPECTIVE_API_REQUEST_LIMIT_FOR_PERIOD
    value: {{ .Values.api.perspectiveApiRequestLimitForPeriod | quote }}
  {{- end }}
  {{- if .Values.api.perspectiveApiRequestLimitPeriodSeconds }}
  - name: PERSPECTIVE_API_REQUEST_LIMIT_PERIOD_SECONDS
    value: {{ .Values.api.perspectiveApiRequestLimitPeriodSeconds | quote }}
  {{- end }}
  {{- if .Values.api.addBigQueryRateLimitsOnProjectCreation }}
  - name: ADD_BIG_QUERY_RATE_LIMITS_ON_PROJECT_CREATION
    value: {{ .Values.api.addBigQueryRateLimitsOnProjectCreation | quote }}
  {{- end }}
  {{- if .Values.api.danekCostPer100kResultsDict }}
  - name: DANEK_COST_PER_100K_RESULTS_DICT
    value: {{ .Values.api.danekCostPer100kResultsDict | quote }}
  {{- end }}
  {{- if .Values.api.supersetApiUrl }}
  - name: SUPERSET_API_URL
    value: {{ tpl ( .Values.api.supersetApiUrl ) . | quote }}
  {{- end }}
  {{- if .Values.api.supersetDatabaseUuid }}
  - name: SUPERSET_DATABASE_UUID
    value: {{ .Values.api.supersetDatabaseUuid | quote }}
  {{- end }}
  {{- if .Values.api.supersetServiceAccountEmail }}
  - name: SUPERSET_SERVICE_ACCOUNT_EMAIL
    value: {{ .Values.api.supersetServiceAccountEmail | quote }}
  {{- end }}
  {{- if .Values.api.supersetDatabaseSqlalchemyUri }}
  - name: SUPERSET_DATABASE_SQLALCHEMY_URI
    value: {{ .Values.api.supersetDatabaseSqlalchemyUri | quote }}
  {{- end }}
  {{- if .Values.api.huggingFaceModelsWhitelist }}
  - name: HUGGING_FACE_MODELS_WHITELIST
    value: {{ .Values.api.huggingFaceModelsWhitelist | quote }}
  {{- end }}
## This is the secret that is used to store the GCP service account json
{{- if .Values.gcp_service_account.enabled }}
volumeMounts:
- name: gcp-creds
  mountPath: /var/secrets/google
  readOnly: true
{{- end }}
{{- end -}}
