# Lesson 05 RFC 7938 Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure lesson 05 to properly follow RFC 7938's ASN model (shared spine ASN), fix 10 technical inaccuracies, and add a new script section on iBGP vs eBGP.

**Architecture:** All spines share AS 65000. Leaves keep unique ASNs 65001-65004. Script gains a new Section 2 (BGP Design Choices) and existing sections are renumbered. All content files (script, README, exercises, solutions) and config files (gNMIc JSON) are updated to match.

**Tech Stack:** Markdown (script/docs), JSON (gNMIc configs), YAML (containerlab topology)

**Spec:** `docs/plans/2026-03-22-lesson-05-rfc7938-restructure-design.md`

---

## File Map

All paths relative to `lessons/clab/05-spine-leaf-bgp/`.

| File | Action | Responsibility |
|------|--------|---------------|
| `gnmic/configs/spine1-bgp.json` | Modify | ASN 65100 -> 65000 |
| `gnmic/configs/spine2-bgp.json` | Modify | ASN 65101 -> 65000 |
| `gnmic/configs/leaf1-bgp.json` | Modify | peer-as 65100/65101 -> 65000 |
| `gnmic/configs/leaf2-bgp.json` | Modify | peer-as 65100/65101 -> 65000 |
| `gnmic/configs/leaf3-bgp.json` | Modify | peer-as 65100/65101 -> 65000 |
| `gnmic/configs/leaf4-bgp.json` | Modify | peer-as 65100/65101 -> 65000 |
| `topology/lab.clab.yml` | Modify | Comment header ASN update |
| `script.md` | Rewrite | Full script restructure |
| `README.md` | Modify | ASN refs, video outline, framing |
| `exercises/README.md` | Modify | ASN refs, exercise 4 fix |
| `solutions/README.md` | Modify | ASN refs in output, exercise 4 fix |
| `gnmic/**[VOICEOVER` (garbage) | Delete | Cleanup |
| `gnmic/10 containers are up...` (garbage) | Delete | Cleanup |
| `gnmic/Six gNMIc commands...` (garbage) | Delete | Cleanup |

---

### Task 1: Update gNMIc configs -- spine ASNs

**Files:**
- Modify: `gnmic/configs/spine1-bgp.json:50`
- Modify: `gnmic/configs/spine2-bgp.json:50`

- [ ] **Step 1: Update spine1-bgp.json**

Change `"autonomous-system": 65100` to `"autonomous-system": 65000` on line 50.

- [ ] **Step 2: Update spine2-bgp.json**

Change `"autonomous-system": 65101` to `"autonomous-system": 65000` on line 50.

- [ ] **Step 3: Verify both spine configs match**

Both files should now have identical ASN (65000) but different router-id values (10.0.1.1 vs 10.0.1.2) and different neighbor peer-address IPs. Everything else (policies, multipath, group name) should be identical.

- [ ] **Step 4: Commit**

```bash
git add gnmic/configs/spine1-bgp.json gnmic/configs/spine2-bgp.json
git commit -m "fix(lesson-05): update spine ASNs to shared 65000 per RFC 7938"
```

---

### Task 2: Update gNMIc configs -- leaf peer-as values

**Files:**
- Modify: `gnmic/configs/leaf1-bgp.json:70-71`
- Modify: `gnmic/configs/leaf2-bgp.json:70-71`
- Modify: `gnmic/configs/leaf3-bgp.json:70-71`
- Modify: `gnmic/configs/leaf4-bgp.json:70-71`

- [ ] **Step 1: Update leaf1-bgp.json**

Line 70: change `"peer-as": 65100` to `"peer-as": 65000`
Line 71: change `"peer-as": 65101` to `"peer-as": 65000`

- [ ] **Step 2: Update leaf2-bgp.json**

Same change: both spine neighbor `peer-as` values from 65100/65101 to 65000.

- [ ] **Step 3: Update leaf3-bgp.json**

Same change.

- [ ] **Step 4: Update leaf4-bgp.json**

Same change.

- [ ] **Step 5: Verify all leaf configs**

Each leaf config should have two neighbors, both with `"peer-as": 65000`. The leaf's own `autonomous-system` values (65001-65004) should be unchanged.

- [ ] **Step 6: Commit**

```bash
git add gnmic/configs/leaf*.json
git commit -m "fix(lesson-05): update leaf peer-as to shared spine ASN 65000"
```

---

### Task 3: Update topology comment and delete garbage files

**Files:**
- Modify: `topology/lab.clab.yml:1-8`
- Delete: `gnmic/**[VOICEOVER`
- Delete: `gnmic/10 containers are up. Let's verify that cross-leaf connectivity doesn't work yet -- without BGP, the leaves don't know about each other's host subnets.`
- Delete: `gnmic/Six gNMIc commands, one per router. Each config file creates the export-connected policy and enables BGP with the correct AS, router-ID, peer-group, and neighbors.`

- [ ] **Step 1: Update topology comment header**

Replace lines 1-8 of `topology/lab.clab.yml`:

```yaml
# Lesson 5: Spine-Leaf Networking with BGP -- 2-Spine + 4-Leaf Clos Fabric
#
#      spine1 (AS 65000)    spine2 (AS 65000)
#       / |  \    \          / |   \    \
#    leaf1 leaf2 leaf3  leaf4
#  (65001)(65002)(65003)(65004)
#     |      |      |      |
#   host1  host2  host3  host4
```

- [ ] **Step 2: Delete garbage files in gnmic/**

```bash
cd lessons/clab/05-spine-leaf-bgp
rm 'gnmic/**[VOICEOVER'
rm 'gnmic/10 containers are up. Let'\''s verify that cross-leaf connectivity doesn'\''t work yet -- without BGP, the leaves don'\''t know about each other'\''s host subnets.'
rm 'gnmic/Six gNMIc commands, one per router. Each config file creates the export-connected policy and enables BGP with the correct AS, router-ID, peer-group, and neighbors.'
```

- [ ] **Step 3: Commit**

```bash
git add topology/lab.clab.yml
git add -A gnmic/  # picks up deletions
git commit -m "fix(lesson-05): update topology ASN comments, delete garbage files"
```

---

### Task 4: Rewrite script.md

This is the largest task. The changes touch most sections but some content is preserved. Apply the edits below as a single pass through the file.

**Files:**
- Modify: `script.md`

**Important context for the implementer:**
- The spec is at `docs/plans/2026-03-22-lesson-05-rfc7938-restructure-design.md` -- read it for the full narrative design of each section.
- **All line numbers below reference the ORIGINAL file before any edits.** Since Step 3 inserts a new section, all subsequent line numbers will shift. Apply changes in document order (top to bottom) in a single pass, or read the full file first and write the complete result.
- The opening hook (lines 33-39) was already fixed in a prior PR and must NOT be changed.
- Pre-Recording Checklist (lines 15-28) stays unchanged.
- Commands, SR Linux CLI snippets, and the overall demo flow (deploy, configure, verify, break, fix) stay unchanged.
- The closing section (lines 248-258) stays unchanged.
- "Drop AFI-SAFI jargon" applies to voiceover/narration text only. SR Linux CLI commands use `afi-safi` as the YANG path -- those must stay as-is.

- [ ] **Step 1: Update lesson information table**

Line 9: change `12-14 minutes` to `13-15 minutes`

- [ ] **Step 2: Rewrite Section 1 (Why Spine-Leaf?)**

Replace lines 43-63 with rewritten Section 1. Key changes per spec:
- Open with lesson 04's actual progression: started hub-and-spoke, exercise 3 added srl2-srl3 making it a full mesh of 3
- One sentence: full mesh gives redundancy but doesn't scale -- don't extrapolate to 50 routers
- Pivot to 3-tier/STP as the real predecessor
- Clos: all links active via ECMP, predictable hop count, tiers scale independently
- Define Clos: "named after Charles Clos, who published this non-blocking switch design in 1953"
- Key points updated to remove "Full mesh: link count grows as N*(N-1)/2"
- Visual updated to reflect new framing

New voiceover text:

> "By the end of lesson 4, our 3 routers were fully meshed -- every router directly connected to every other. That gives you redundancy, but it only works at small scale. Real data centers with hundreds of racks never tried to full-mesh their switches.
>
> Instead, they used a 3-tier architecture: core, distribution, and access layers. But those designs relied on Spanning Tree Protocol, which blocks redundant links to prevent loops. You pay for redundant cables, then STP disables half of them. Wasteful.
>
> Clos spine-leaf architecture -- named after Charles Clos, who published this non-blocking switch design in 1953 -- solves this. You split the network into two tiers: spines and leaves. Every leaf connects to every spine, but there are no leaf-to-leaf or spine-to-spine links. Every path between any two leaves crosses exactly one spine. And because all paths are equal length, the router can use ECMP -- equal-cost multipath -- to load-balance across all spines simultaneously. No blocked links. No wasted bandwidth.
>
> The key insight: to add more bandwidth, add more spines. To add more servers, add more leaves. Each tier scales independently."

Key points:
- 3-tier + STP: blocks redundant links, wastes capacity
- Clos (Charles Clos, 1953): structured 2-tier, all links active via ECMP, tiers scale independently
- Horizontal scaling: spines add bandwidth, leaves add server ports

- [ ] **Step 3: Add new Section 2 (BGP Design Choices)**

Insert after Section 1 (after the `---` separator). This is entirely new content.

Section heading: `### Section 2: BGP Design Choices (90 seconds)`

Voiceover text:

> "We need a routing protocol for this fabric. Lesson 4 used eBGP -- external BGP. Could we use iBGP -- internal BGP -- instead? If every device shared one AS number, all sessions would be iBGP. But iBGP has a catch: a router will not re-advertise a route learned from one iBGP peer to another. If leaf1 tells spine1 about its host subnet, spine1 would not pass it to leaf2. To fix this, you'd need either a full mesh of iBGP sessions between all devices, or a route reflector -- a designated router that's allowed to break that rule. Both add complexity.
>
> RFCs -- Requests for Comments -- are how the internet's protocols are documented and standardized. They are the primary source of truth for how things actually work. If you take one habit from this course, make it reading RFCs.
>
> RFC 7938, published in 2016, documents how large-scale data centers like Microsoft and Facebook solved this: use eBGP for everything. eBGP requires different AS numbers on each side of a session -- that's what makes it external. So each leaf gets its own ASN. The spines share a single ASN -- they never peer with each other, so there's no iBGP between them. Every spine-leaf link crosses an AS boundary, making it eBGP.
>
> The result: routes are re-advertised freely, no route reflectors needed. Loop prevention comes free through AS-path. And because all spines share one ASN, the AS-path through any spine looks identical -- which is exactly what ECMP needs to treat them as equal-cost paths."

Key points:
- iBGP won't re-advertise between peers without route reflectors
- RFC 7938: eBGP-only underlay, unique ASN per leaf, shared ASN for all spines
- Shared spine ASN gives identical AS-paths = natural ECMP

Transition: "Let's look at the specific design of our fabric."

- [ ] **Step 4: Rewrite Section 3 (Our Fabric, was Section 2)**

Replace the old Section 2 (lines 66-94). New heading: `### Section 3: Our Fabric (90 seconds)`

Remove the old "Why a unique AS per device?" paragraph entirely (covered in Section 2).

Updated voiceover text:

> "Here's our fabric: 2 spines, 4 leaves, 4 hosts. Every leaf connects to every spine -- that's 8 links. Each link gets a /31 point-to-point subnet, just like lesson 4. Each leaf also connects to one host on a /24 subnet.
>
> Both spines share AS 65000. Leaves are AS 65001 through 65004 -- each leaf its own autonomous system, as RFC 7938 recommends. Every spine-leaf link is an eBGP session. A peer-group is a template that applies the same BGP settings to multiple neighbors. The spines' peer-group is called 'leaves' with 4 neighbors each. The leaves' peer-group is called 'spines' with 2 neighbors each. Total: 8 BGP sessions across the fabric.
>
> Each router also gets a router-ID -- a unique 32-bit identifier, set to a loopback-style IP, that BGP uses to identify the router in the network."

Update ASCII diagram:
```
     spine1 (AS 65000)    spine2 (AS 65000)
       / |    \    \       / |    \    \
    leaf1  leaf2  leaf3  leaf4
  (65001) (65002) (65003) (65004)
     |       |       |       |
   host1   host2   host3   host4
```

Updated key points:
- /31 point-to-point links between every spine-leaf pair
- RFC 7938: shared spine ASN (65000), unique leaf ASNs (65001-65004), every link is eBGP
- 8 total BGP sessions (4 leaves x 2 spines)
- Shared spine ASN gives identical AS-paths, enabling ECMP

Transition: "Let's deploy this and see it work."

- [ ] **Step 5: Renumber Section 4 (Deploying the Fabric, was Section 3)**

Change heading from `### Section 3: Deploying the Fabric (2 minutes)` to `### Section 4: Deploying the Fabric (2 minutes)`. No content changes.

- [ ] **Step 6: Rewrite Section 5 (Configure and Verify, was Section 4)**

Change heading from `### Section 4: Live Demo -- Configure and Verify (3 minutes)` to `### Section 5: Live Demo -- Configure and Verify (3 minutes)`.

Replace the voiceover at line 126-128 with expanded policy explanation:

> "Six gNMIc commands, one per router. Each config file creates three routing policies and chains them together -- same pattern we used in lesson 4, but worth a closer look now that 6 routers depend on it.
>
> The export policies are chained as a list: export-connected runs first. If a route is a connected host /24 matching the host-subnets prefix-set, accept it. If not, the next-policy default action passes it to export-bgp, which accepts BGP-learned routes. This chain is what makes spines work as transit routers -- without export-bgp, a spine would learn leaf1's host subnet but never announce it to the other leaves. SR Linux has a default-deny export policy, so nothing gets advertised unless you explicitly allow it.
>
> The host-subnets prefix-set filters out /31 fabric link prefixes from export-connected -- those are already known via direct connection on each router and don't need to be in BGP. Only the /24 host subnets get advertised.
>
> Each config also enables the IPv4 unicast address family with multipath for ECMP, and configures BGP with the correct AS, router-ID, peer-group, and neighbors."

Commands stay the same (lines 130-138).

Replace the TTL narration at line 171:

> "All three succeed. host1 can reach host2, host3, and host4 -- all on different leaves, all going through the spine tier. Notice TTL is 61: starting at 64, decremented once by each of the 3 routers in the path -- leaf1, the spine, and leaf4. The leaf-to-leaf path is 2 fabric hops, but hosts see 3 router hops end-to-end."

- [ ] **Step 7: Rewrite Section 6 (Spine Failure, was Section 5)**

Change heading from `### Section 5: Live Demo -- Spine Failure (2 minutes)` to `### Section 6: Live Demo -- Spine Failure (2 minutes)`.

Replace the convergence narration at line 203:

> "A few packets lost during BGP convergence, then it recovers. Recovery is fast here because disabling an interface triggers an immediate TCP teardown -- the BGP session drops instantly. In a production fabric, you'd configure BFD -- Bidirectional Forwarding Detection -- for sub-second failure detection. Without it, BGP's default hold timer is 90 seconds, meaning it could take that long to notice a neighbor is gone. All traffic now flows through spine2. Let's check the routing table."

All commands and remaining narration stay the same.

- [ ] **Step 8: Rewrite Recap**

Replace lines 234-244 with:

> "Let's recap:
>
> - Clos spine-leaf -- named after Charles Clos's 1953 design -- is a structured 2-tier topology with predictable latency and all links active via ECMP.
> - RFC 7938 recommends eBGP for the underlay because it re-advertises routes freely without needing route reflectors. Spines share a single ASN, each leaf gets its own. Every spine-leaf link is eBGP.
> - ECMP works naturally because the shared spine ASN produces identical AS-paths through any spine. But SR Linux requires explicit multipath maximum-paths configuration to enable it.
> - Export policy chaining makes it all work: export-connected advertises host subnets, export-bgp enables transit through spines. SR Linux's default-deny export means nothing advertises without explicit policy.
> - Spine failures degrade capacity but not connectivity. Fast recovery depends on interface-level detection or BFD, not BGP's 90-second hold timer.
> - This is the architecture under every major cloud and Kubernetes deployment. When you troubleshoot pod networking, this is what's underneath."

- [ ] **Step 9: Update post-recording checklist and editing notes**

Line 265: change `~12-14 minutes` to `~13-15 minutes`

Replace editing notes (lines 283-290) with updated timestamps:

```
- **0:00-0:30** - Hook, overlay lesson 04 topology diagram
- **0:30-2:30** - Why spine-leaf, STP comparison diagrams
- **2:30-4:00** - BGP design choices: iBGP vs eBGP, RFC 7938, shared spine ASN
- **4:00-5:30** - Our fabric: topology diagram with AS numbers and addressing
- **5:30-7:30** - Deploy fabric, show 10 containers and failed ping (no BGP yet)
- **7:30-10:30** - Configure BGP, policy chain explanation, verify sessions, ECMP routing table, pings
- **10:30-12:30** - Spine failure demo, convergence timing, ping loss/recovery, restore
- **12:30-13:00** - Recap bullet points overlay
- **13:00-13:30** - Closing, exercises call-to-action, EVPN/VXLAN teaser
```

- [ ] **Step 10: Commit**

```bash
git add script.md
git commit -m "feat(lesson-05): restructure script for RFC 7938 compliance and accuracy fixes"
```

---

### Task 5: Update README.md

**Files:**
- Modify: `README.md`

**Important context for the implementer:**
- Read the current README.md first. It's ~330 lines.
- The spec lists all required changes. Key: every instance of "ASN-per-device", "unique ASN per device", ASN 65100/65101 must be updated.
- The README adapts the script's voiceover text for written format. When the plan says "match the new script framing," adapt the script's voiceover into concise prose: remove second-person framing ("you"), convert spoken explanations to written paragraphs with markdown formatting. Reference the completed script.md for the source content.

- [ ] **Step 1: Update objectives**

Line 9: change `Explain CLOS/spine-leaf architecture and why it replaced full mesh and 3-tier designs` to `Explain Clos/spine-leaf architecture and why it replaced 3-tier designs in data centers`

Line 13: change `Configure eBGP underlay using RFC 7938 ASN-per-device model` to `Configure eBGP underlay using RFC 7938 (shared spine ASN, unique leaf ASNs)`

- [ ] **Step 2: Rewrite Video Outline Section 1**

Update the "1. Why Spine-Leaf?" section (around lines 28-38) to match the new script framing:
- Remove full-mesh scaling math ("10 devices need 45 links, 50 devices need 1,225")
- Bridge from lesson 04 hub-and-spoke -> full mesh of 3
- Pivot to 3-tier/STP as the real predecessor
- Update the comparison table: remove the "Full mesh" row or reduce it to one line, focus on 3-tier vs Clos
- Add Clos attribution (Charles Clos, 1953)

- [ ] **Step 3: Add Video Outline Section 2 (BGP Design Choices)**

Insert new section after "1. Why Spine-Leaf?" covering:
- iBGP vs eBGP contrast (brief -- 2-3 sentences)
- RFCs as source of truth
- RFC 7938: eBGP with shared spine ASN, unique leaf ASNs
- Why: no route reflectors, free loop prevention, natural ECMP

- [ ] **Step 4: Update Video Outline Section 2 -> 3 (Clos Topology Design)**

Rename to "3. Our Fabric" and update:
- Both spines AS 65000
- Change "RFC 7938 eBGP with ASN-per-device" to "RFC 7938 eBGP with shared spine ASN"
- Define peer-group and router-ID in the text

- [ ] **Step 5: Update Video Outline Section 5 (Spine Failure)**

Replace `docker stop/start` commands (around lines 101-114) with `sr_cli` interface disable/enable approach matching the script and exercises.

- [ ] **Step 6: Update Mermaid diagram**

Change both spine labels from `AS 65100`/`AS 65101` to `AS 65000`.

- [ ] **Step 7: Update BGP Design table**

Update the table (around lines 169-176):
- spine1 ASN: 65100 -> 65000
- spine2 ASN: 65101 -> 65000

- [ ] **Step 8: Update Routing Policies section and BGP Multipath section**

No ASN changes needed here, but verify the text doesn't reference old ASN values.

- [ ] **Step 9: Update "Why This Matters for Kubernetes" table**

Change "ASN-per-device (RFC 7938)" to "RFC 7938 eBGP (shared spine ASN, unique leaf ASNs)" and update the Kubernetes equivalent text.

- [ ] **Step 10: Search for any remaining "65100", "65101", "ASN-per-device", or "unique ASN per device"**

Run: `grep -n '65100\|65101\|ASN-per-device\|unique ASN' README.md`

Fix any remaining instances.

- [ ] **Step 11: Commit**

```bash
git add README.md
git commit -m "fix(lesson-05): update README for RFC 7938 shared spine ASN model"
```

---

### Task 6: Update exercises/README.md

**Files:**
- Modify: `exercises/README.md`

- [ ] **Step 1: Update Exercise 1 Step 3 (config examination)**

Around line 31, the config examination asks about multipath. Add a question about the shared spine ASN:
- "Why do both spine neighbors have the same peer-as (65000)? What does RFC 7938 say about spine ASN assignment?"

- [ ] **Step 2: Fix Exercise 4 export-policy restoration**

Line 240: change `set / network-instance default protocols bgp group spines export-policy [export-connected]` to `set / network-instance default protocols bgp group spines export-policy [export-connected export-bgp]`

- [ ] **Step 3: Search for remaining old ASN references**

Run: `grep -n '65100\|65101' exercises/README.md`

Fix any remaining instances.

- [ ] **Step 4: Commit**

```bash
git add exercises/README.md
git commit -m "fix(lesson-05): update exercises for shared spine ASN, fix exercise 4 export-policy"
```

---

### Task 7: Update solutions/README.md

**Files:**
- Modify: `solutions/README.md`

This file is ~440 lines with expected CLI output tables. Every ASN reference needs updating.

- [ ] **Step 1: Update all spine ASN references in expected output**

Search and replace:
- `65100` -> `65000` in spine1 context (AS column in neighbor tables, AS-path references)
- `65101` -> `65000` in spine2 context

**Be careful:** leaf ASNs 65001-65004 must NOT be changed. Only spine ASN values.

Specific locations:
- Exercise 1 spine neighbor table (around line 60-77): spine1 shows `AS` column with leaf ASNs -- these are correct. But the `AS 65100` label for spine1 itself needs updating.
- Exercise 1 leaf neighbor table (around line 42-52): peer AS values for spines change from 65100/65101 to 65000/65000.
- Exercise 2 routing table: AS-path references if any.
- Exercise 3 BGP neighbor table showing spine1 session down: peer AS values.
- Exercise 4 fix step.
- Key Takeaways section.

- [ ] **Step 2: Fix Exercise 4 export-policy fix step**

Around line 398: change `set / network-instance default protocols bgp group spines export-policy [export-connected]` to `set / network-instance default protocols bgp group spines export-policy [export-connected export-bgp]`

- [ ] **Step 3: Update Key Takeaway #5**

Around line 436: change "RFC 7938 eBGP with ASN-per-device is the data center standard -- each router gets a unique AS number" to "RFC 7938 eBGP is the data center standard -- spines share a single ASN, each leaf gets its own, and every spine-leaf link is eBGP"

- [ ] **Step 4: Verify with grep**

Run: `grep -n '65100\|65101\|ASN-per-device\|unique ASN' solutions/README.md`

Should return zero matches.

- [ ] **Step 5: Commit**

```bash
git add solutions/README.md
git commit -m "fix(lesson-05): update solutions for shared spine ASN, fix exercise 4 export-policy"
```

---

### Task 8: Final verification and PR

- [ ] **Step 1: Search all files for stale ASN references**

```bash
cd lessons/clab/05-spine-leaf-bgp
grep -rn '65100\|65101' --include='*.md' --include='*.json' --include='*.yml'
```

Should return zero matches.

- [ ] **Step 2: Search for stale "ASN-per-device" language**

```bash
grep -rn 'ASN-per-device\|unique ASN per device' --include='*.md'
```

Should return zero matches.

- [ ] **Step 3: Verify garbage files are gone**

```bash
ls gnmic/ | grep -v configs | grep -v .gnmic.yml
```

Should return nothing.

- [ ] **Step 4: Create PR**

```bash
git push -u origin feature/lesson-05-rfc7938-restructure
gh pr create --base instructor --title "feat(lesson-05): restructure for RFC 7938 compliance" --body "$(cat <<'EOF'
## Summary
- Changed spine ASN model to follow RFC 7938: both spines share AS 65000 (was unique 65100/65101)
- Added new script Section 2 (BGP Design Choices): iBGP vs eBGP contrast, route reflectors, RFC 7938 rationale
- Rewrote Section 1 to bridge from lesson 04's actual topology instead of full-mesh strawman
- Fixed TTL/hop count contradiction, explained export-bgp transit role and policy chaining
- Added convergence timing note (fast-fallover vs hold timer, BFD)
- Fixed exercise 4 export-policy restoration bug
- Defined jargon on first use (Clos, RFC, iBGP, route reflector, peer-group, router-ID)
- Deleted garbage files from gnmic/ directory
- Updated all configs, README, exercises, and solutions to match

## Lesson(s) Affected
- Lesson 05: Spine-Leaf Networking with BGP

## Test plan
- [ ] All gNMIc configs use ASN 65000 for spines
- [ ] No references to 65100 or 65101 remain in any file
- [ ] No "ASN-per-device" language remains
- [ ] Script sections renumbered correctly (1-6)
- [ ] Exercise 4 fix restores [export-connected export-bgp]
- [ ] Topology deploys successfully with containerlab
- [ ] BGP sessions establish with shared spine ASN
EOF
)"
```
