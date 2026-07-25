# southernaiconsulting.com

The public website for **Southern AI Consulting LLC** (Prattville, Alabama).

Static HTML and CSS. No framework, no build step, no dependencies, no
JavaScript, and no external network requests — the page is self-contained, so it
loads instantly and there is nothing to keep updated or patched.

Hosted on **GitHub Pages**. DNS stays at **Namecheap**, which is deliberate: the
nameservers never move, so the Google Workspace email on this domain is never
affected by anything done here.

## Files

| File | What it is |
|---|---|
| `index.html` | The entire site — one page, nine sections, anchor navigation |
| `styles.css` | All styling. Light and dark themes; contrast ratios noted in comments |
| `logo.svg` | The mark on its own, for light backgrounds |
| `logo-lockup.svg` | Mark + wordmark, for email signatures and letterhead |
| `favicon.svg` | Mark on a navy rounded square, for browser tabs |
| `og.png` | 1200×630 link-preview card (Facebook, LinkedIn, texts) |
| `tools/make_og.py` | Regenerates `og.png`. Needs Pillow + macOS Georgia font |
| `CNAME` | Tells GitHub Pages to serve this repo at the custom domain |
| `robots.txt`, `sitemap.xml` | Search-engine basics |
| `404.html` | Branded not-found page |

## Making a change

```sh
# edit, then look at it locally — just open the file, no server needed
open index.html

git add -A
git commit -m "Describe the change"
git push
```

GitHub Pages redeploys automatically, usually within a minute.

## Things you will probably want to change

**Swap the audit button over to the Notion intake form.** Search `index.html`
for `CTA_URL` — three places. Replace the whole `mailto:...` href with the
Notion form's public share URL. The Notion page has to be shared publicly to the
web, not just inside your workspace.

**Retire the founding-client discount** once client #3 signs. Delete the
`<p class="founding">` block in `index.html`.

**Change a price.** Search for `from $1,200` / `from $1,500` / `from $800`.
Prices also appear in the structured-data block at the bottom of `index.html`
(`hasOfferCatalog`) — update both so search engines don't show a stale number.

**Add a testimonial or case study.** These are the highest-value additions once
the first founding clients are delivered.

## DNS (for reference — already done)

At Namecheap → Domain List → Manage → **Advanced DNS**:

| Type | Host | Value |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `stopyellingatme.github.io.` |

**Do not touch the `MX` record (`smtp.google.com`) or the
`google-site-verification` TXT record.** Those are the live business email. If
the site ever needs to be rolled back to a parking page, restore a single `A`
record for `@` pointing at `192.64.119.150`.
