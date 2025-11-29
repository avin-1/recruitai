Here is a detailed reference document that you can feed to your coding agent to **post content to Instagram using Instagram Graph API**, given that you already have a valid access token. I describe the required setup, constraints, and full flow (with sample API calls).

---

## Overview & Prerequisites

* Instagram Graph API publishing works only for **Instagram Business (Professional)** accounts — not personal profiles. ([Stack Overflow][1])
* Your Instagram Business account must be linked to a **Facebook Page**. ([Phyllo][2])
* You need a Facebook developer app configured with the **Instagram Graph API** product enabled. ([Medium][3])
* The access token must have required permissions: at least `instagram_basic` and `instagram_content_publish` (and page-level permissions via the linked Facebook Page). ([Medium][3])
* Only certain media types and formats are supported: for example, photos must be JPEG. Other media types (or video, carousel) may have additional constraints. ([Medium][4])
* There are rate limits: e.g. up to 25 API-published posts per 24h per account. ([Medium][4])

---

## High-Level Flow to Create & Publish a Post

To publish a post (e.g. an image) via Instagram Graph API, you must perform **two sequential steps**:

1. **Create a media container** — upload or reference the media, get back a container/creation ID.
2. **Publish** the media container to make the actual post appear on Instagram feed. ([Facebook Developers][5])

Optionally: check status of container before publish; check publishing limits. ([GitHub][6])

---

## API Endpoints & Required Parameters

| Endpoint                                     | Method | Purpose                                                | Required / Important Params                                                                                                                                                                                    |
| -------------------------------------------- | ------ | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `POST /{ig-user-id}/media`                   | POST   | Create media container (upload or reference media)     | `image_url` (publicly accessible URL to the media), or `media_type`, `video_url` (for video), plus optional `caption`, `caption_hashtags`, `location_id`, etc., and `access_token`. ([Facebook Developers][5]) |
| `POST /{ig-user-id}/media_publish`           | POST   | Publish a previously created media container           | `creation_id` (returned ID from previous step), `access_token` ([Facebook Developers][7])                                                                                                                      |
| `GET /{ig-container-id}?fields=status_code`  | GET    | Check status of media container (optional)             | `fields=status_code`, `access_token` ([GitHub][6])                                                                                                                                                             |
| `GET /{ig-user-id}/content_publishing_limit` | GET    | Check how many API-published posts remain (rate limit) | `access_token` ([GitHub][6])                                                                                                                                                                                   |

Key: `ig-user-id` is the Instagram Business account’s ID, not your Facebook Page ID — you must fetch this ID after linking your IG account to FB Page. ([Jamie Maguire][8])

---

## Detailed Step-by-Step Guide (Pseudo / Sample HTTP Calls)

Assuming you have:

* `ACCESS_TOKEN` (valid, with correct scopes)
* `IG_USER_ID` (the Instagram Business account ID)
* A publicly accessible media URL (say an image hosted somewhere).

### 1. Create Media Container

```http
POST https://graph.instagram.com/{IG_USER_ID}/media
Content-Type: application/json

{
  "image_url": "https://yourserver.com/path/to/image.jpg",
  "caption": "This is my post caption — #tag1 #tag2",
  "access_token": "ACCESS_TOKEN"
}
```

**Response** (on success): JSON with `"id"` — this is your `creation_id`.

If you’re uploading video or using other media types, include appropriate params (e.g. `media_type`, `video_url`).

### 2. (Optional) Check Container Status

```http
GET https://graph.instagram.com/{creation_id}?fields=status_code&access_token=ACCESS_TOKEN
```

Response contains `status_code`: make sure it’s valid before publishing.

### 3. Publish Media Container

```http
POST https://graph.instagram.com/{IG_USER_ID}/media_publish
Content-Type: application/json

{
  "creation_id": "CREATION_ID_FROM_STEP1",
  "access_token": "ACCESS_TOKEN"
}
```

**Response**: JSON confirming success, with ID of the published media (post).

### 4. (Optional) Track Rate Limit

```http
GET https://graph.instagram.com/{IG_USER_ID}/content_publishing_limit?access_token=ACCESS_TOKEN
```

Use this to ensure you don’t exceed allowed API-published posts (e.g. 25 per 24 hrs).

---

## Important Constraints & Limitations (to embed in your agent)

* Only **Business Instagram Accounts** work. Creator accounts may not be supported in all cases. ([Stack Overflow][1])
* Media must be **accessible via public URL**. Local files on disk cannot be sent directly — they must be uploaded somewhere reachable from Instagram servers. ([Stack Overflow][9])
* Only certain formats supported: JPEG for images. Other formats may fail. ([Medium][4])
* Rate limit: ~25 API-published posts / 24 hours per account. Your agent should track and enforce this. ([Medium][4])
* Not all post types are supported: e.g. Stories, IGTV, some advanced features (shopping tags, filters, carousels in some cases) may not be allowed. ([Medium][4])

---

## Sample Flow in Pseudocode (for your Agent)

```
function postToInstagram(imageUrl, caption) {
    creation = POST /{IG_ID}/media { image_url: imageUrl, caption: caption, access_token: TOKEN }
    if creation.id missing: error

    // optional: check status
    status = GET /{creation.id}?fields=status_code
    if status_code not OK: error

    publish = POST /{IG_ID}/media_publish { creation_id: creation.id, access_token: TOKEN }
    if publish success: return publish.id
    else error
}
```

Agent should also fetch and store content publishing limit and decrement after each post, to enforce rate limiting.

---

## What Your Agent Needs to Know / Do Before Running

* Must confirm account is Business + linked to FB Page + correct permissions.
* Media must be hosted with a publicly accessible URL (e.g. you upload images to your server or cloud storage first).
* Use stable, immutable long-lived access token (or refresh token logic) to avoid expiry.
* Handle error scenarios from API (invalid token, rate limit exceeded, unsupported media format, etc.).
* Respect content-publishing rate limits.

---

## References (Docs & Reading)

* Instagram Graph API — Content Publishing guide / reference for `/media` and `/media_publish`. ([Facebook Developers][7])
* Blog / tutorial summarizing publishing via API (with constraints & limitations). ([Medium][10])
* Real-world community experiences (e.g. limitations, media URL requirement). ([Stack Overflow][9])

---

If you like — I can **produce a ready-to-use spec file** (e.g. **OpenAPI / Swagger or Postman collection JSON**) for these endpoints — so your coding agent can **directly import** and use it.
Do you want me to generate that for you now?

[1]: https://stackoverflow.com/questions/49025215/share-image-from-my-website-to-instagram-using-instagram-graph-api?utm_source=chatgpt.com "share image from my website to instagram using ..."
[2]: https://www.getphyllo.com/post/how-to-use-instagram-api-to-post-photos-on-instagram?utm_source=chatgpt.com "How To Use Instagram API To Post Photos On Instagram"
[3]: https://vdelacou.medium.com/posting-to-instagram-programmatically-cc69bf1effa8?utm_source=chatgpt.com "Posting to Instagram Programmatically | by Vincent Delacourt"
[4]: https://datkira.medium.com/instagram-graph-api-overview-content-publishing-limitations-and-references-to-do-quickly-99004f21be02?utm_source=chatgpt.com "Instagram Graph API: Overview, Content Publishing ..."
[5]: https://developers.facebook.com/docs/instagram-platform/content-publishing/?utm_source=chatgpt.com "Publish Content - Instagram Platform - Meta for Developers"
[6]: https://github.com/adminazhar/instagram-upload-image-api?utm_source=chatgpt.com "adminazhar/instagram-upload-image-api"
[7]: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish/?utm_source=chatgpt.com "Media Publish - Instagram Platform - Meta for Developers"
[8]: https://jamiemaguire.net/index.php/2019/05/28/tapping-into-the-instagram-graph-api-part-1-introducing-the-instagram-graph-api-and-how-do-you-connect-to-it/?utm_source=chatgpt.com "Introducing the Instagram Graph API and how do you connect ..."
[9]: https://stackoverflow.com/questions/71877259/how-to-upload-image-saved-in-local-device-to-instagram-graph-api?utm_source=chatgpt.com "How to upload image saved in local device to Instagram ..."
[10]: https://stefan-poeltl.medium.com/publish-media-to-instagram-via-the-instagram-graph-api-68664d7a5c0c?utm_source=chatgpt.com "Publish media to Instagram via the Instagram Graph API"
