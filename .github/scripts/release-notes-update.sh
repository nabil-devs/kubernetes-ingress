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

release_notes_content=$(${ROOTDIR}/.github/scripts/pull-release-notes.py ${ic_version} ${helm_chart_version} ${k8s_versions} "${release_date}")
if [ $? -ne 0 ]; then
    echo "ERROR: failed processing release notes"
    exit 2
fi

if [ -z "${release_notes_content}" ]; then
    echo "ERROR: no release notes content"
    exit 2
fi

# update releases docs
file_path=${DOCS_TO_UPDATE_FOLDER}/releases.md
if [ "${DEBUG}" != "false" ]; then
    echo "Processing ${file_path}"
fi
file_name=$(basename "${file_path}")
mv "${file_path}" "${TMPDIR}/${file_name}"
head -n 8 "${TMPDIR}/${file_name}" > "${TMPDIR}/header"
tail -n +9 "${TMPDIR}/${file_name}" > "${TMPDIR}/body"
echo "${release_notes_content}" > "${TMPDIR}/release_notes"
cat "${TMPDIR}/header" "${TMPDIR}/release_notes" "${TMPDIR}/body" > "${file_path}"
if [ $? -ne 0 ]; then
    echo "ERROR: failed processing ${file_path}"
    mv "${TMPDIR}/${file_name}" "${file_path}"
    exit 2
fi
rm -rf "${TMPDIR}/header" "${TMPDIR}/body" "${TMPDIR}/release_notes"
