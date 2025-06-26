#!/usr/bin/env python

import argparse
import json
import os
import re

from github import Auth, Github
from jinja2 import Environment, FileSystemLoader

# parse args
parser = argparse.ArgumentParser()
parser.add_argument("nic_version", help="NGINX Ingress Controller version")
parser.add_argument("helm_chart_version", help="NGINX Ingress Controller Helm chart version")
parser.add_argument("k8s_versions", help="Kubernetes versions")
parser.add_argument("release_date", help="Release date")
args = parser.parse_args()
NIC_VERSION = args.nic_version
HELM_CHART_VERSION = args.helm_chart_version
K8S_VERSIONS = args.k8s_versions
RELEASE_DATE = args.release_date

# Set up Jinja2 environment
template_dir = os.path.dirname(os.path.abspath(__file__))
env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template("release-notes.j2")


def parse_sections(markdown: str):
    sections = {}
    current = None
    for line in markdown.splitlines():
        if line.startswith("### "):
            current = line[3:].strip()
            sections[current] = []
        elif (current and line.strip().startswith("* ")) and "made their first contribution" not in line:
            sections[current].append(line.strip()[2:].strip())
    return sections


token = os.environ.get("GITHUB_TOKEN")

# using an access token
auth = Auth.Token(token)

# Public Web Github
g = Github(auth=auth)

# Then play with your Github objects:
ORG = os.getenv("GITHUB_ORG", "nginx")
REPO = os.getenv("GITHUB_REPO", "kubernetes-ingress")

repo = g.get_organization(ORG).get_repo(REPO)
release = None
releases = repo.get_releases()
for rel in releases:
    if rel.tag_name == f"v{NIC_VERSION}":
        release = rel
        break

# 4. Print out the notes
if release is not None:
    sections = parse_sections(release.body or "")

    # print(json.dumps(sections))

    catagories = {}
    dependencies_title = ""
    for title, changes in sections.items():
        if any(x in title for x in ["Other Changes", "Documentation", "Maintenance", "Tests"]):
            continue
        parsed = []
        go_dependencies = []
        docker_dependencies = []
        for line in changes:
            change = re.search("^(.*) by @.* in (.*)$", line)
            change_title = change.group(1)
            pr_link = change.group(2)
            pr_number = re.search(r"^.*pull/(\d+)$", pr_link).group(1)
            if "Dependencies" in title:
                dependencies_title = title
                if "go group" in change_title or "go_modules group" in change_title:
                    change_title = "Bump Go dependencies"
                    pr = {"details": f"[{pr_number}]({pr_link})", "title": change_title}
                    go_dependencies.append(pr)
                elif (
                    "Docker image update" in change_title
                    or "docker group" in change_title
                    or "docker-images group" in change_title
                    or "in /build" in change_title
                ):
                    change_title = "Bump Docker dependencies"
                    pr = {"details": f"[{pr_number}]({pr_link})", "title": change_title}
                    docker_dependencies.append(pr)
                else:
                    pr = f"[{pr_number}]({pr_link}) {change_title.capitalize()}"
                    parsed.append(pr)
            else:
                pr = f"[{pr_number}]({pr_link}) {change_title.capitalize()}"
                parsed.append(pr)

        catagories[title] = parsed

    # print(catagories[dependencies_title])
    go_dep_prs = "".join([f"{dep['details']}, " for dep in go_dependencies])
    docker_dep_prs = "".join([f"{dep['details']}, " for dep in docker_dependencies])
    go_dep_prs = f"{go_dep_prs.rstrip(', ')} {go_dependencies[0]['title']}"
    docker_dep_prs = f"{docker_dep_prs.rstrip(', ')} {docker_dependencies[0]['title']}"

    x = go_dep_prs.rsplit(",", 1)
    go_dep_prs = " &".join(x)

    x = docker_dep_prs.rsplit(",", 1)
    docker_dep_prs = " &".join(x)

    catagories[dependencies_title].append(docker_dep_prs)
    catagories[dependencies_title].append(go_dep_prs)
    catagories[dependencies_title].reverse()

data = {
    "version": NIC_VERSION,
    "release_date": RELEASE_DATE,
    "sections": catagories,
    "HELM_CHART_VERSION": HELM_CHART_VERSION,
    "K8S_VERSIONS": K8S_VERSIONS,
}

# Render with Jinja2
print(template.render(**data))

# To close connections after use
g.close()
