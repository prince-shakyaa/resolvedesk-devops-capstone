{{/* Chart name */}}
{{- define "resolvedesk.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Fully qualified app name: "<release>" when the release is named after the chart, else "<release>-<chart>". */}}
{{- define "resolvedesk.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "resolvedesk.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "resolvedesk.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Selector labels for a component. Usage: include "resolvedesk.selectorLabels" (dict "root" . "component" "backend") */}}
{{- define "resolvedesk.selectorLabels" -}}
app.kubernetes.io/name: {{ include "resolvedesk.name" .root }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{- define "resolvedesk.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "resolvedesk.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "resolvedesk.postgresSecretName" -}}
{{- default (printf "%s-postgres" (include "resolvedesk.fullname" .)) .Values.postgres.existingSecret }}
{{- end }}

{{- define "resolvedesk.backendName" -}}{{ include "resolvedesk.fullname" . }}-backend{{- end }}
{{- define "resolvedesk.frontendName" -}}{{ include "resolvedesk.fullname" . }}-frontend{{- end }}
{{- define "resolvedesk.postgresName" -}}{{ include "resolvedesk.fullname" . }}-postgres{{- end }}
