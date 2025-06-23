#!/usr/bin/env bash

set -o pipefail

ROOTDIR=$(git rev-parse --show-toplevel || echo ".")
TMPDIR=/tmp
DEBUG=${DEBUG:-"false"}

 usage() {
    echo "Usage: $0 <docs_to_update_folder> <ic_version> <helm_chart_version> <k8s_versions> <release_date>"
    exit 1
 }

 # clone local doc repo
 # if branch for the release doesnt exist, create it, otherwise checkout

DOCS_TO_UPDATE_FOLDER=$1
ic_version=$2
helm_chart_version=$3
k8s_versions=$4
release_date=$5

if [ -z "${DOCS_TO_UPDATE_FOLDER}" ]; then
    usage
fi

if [ -z "${ic_version}" ]; then
    usage
fi

if [ -z "${helm_chart_version}" ]; then
    usage
fi

if [ -z "${k8s_versions}" ]; then
    usage
fi

if [ -z "${release_date}" ]; then
    usage
fi

# update releases docs
file_path=${DOCS_TO_UPDATE_FOLDER}/releases.md
if [ "${DEBUG}" != "false" ]; then
    echo "Processing ${file_path}"
fi
file_name=$(basename "${file_path}")
mv "${file_path}" "${TMPDIR}/${file_name}"
sed -e "8r ${ROOTDIR}/hack/changelog-template.txt" "${TMPDIR}/${file_name}" | sed \
    -e "s/%%TITLE%%/## $ic_version/g" \
    -e "s/%%IC_VERSION%%/$ic_version/g" \
    -e "s/%%HELM_CHART_VERSION%%/$helm_chart_version/g" \
    -e "s/%%K8S_VERSIONS%%/$k8s_versions.\n/g" \
    -e "s/%%RELEASE_DATE%%/$release_date/g" \
    > ${file_path}
if [ $? -ne 0 ]; then
    echo "ERROR: failed processing ${file_path}"
    mv "${TMPDIR}/${file_name}" "${file_path}"
    exit 2
fi
