{{- define "notes-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "notes-chart.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "notes-chart.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Labels every object carries. app.kubernetes.io/* are the conventional
     names, and managed-by lets you find everything Helm owns. */}}
{{- define "notes-chart.labels" -}}
app.kubernetes.io/name: {{ include "notes-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{/* Only the labels used for Pod selection. These must NOT include version,
     or a chart upgrade changes the selector - which is immutable. */}}
{{- define "notes-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "notes-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
