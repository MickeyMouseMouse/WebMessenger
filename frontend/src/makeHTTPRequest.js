export default async function makeHTTPRequest(url, method, payload = null) {
  let header = {}
  let body = null
  if (payload != null) {
    if (payload.constructor === ({}).constructor) {
      body = JSON.stringify(payload)
      header = {"Content-Type": "application/json"}
    } else {
      body = payload
    }
  }
  let r = await httpRequest(url, method, header, body)
  /*
  if (r.status == 401) { // access-token expired
    let refresh_r = await httpRequest("/auth/refresh", "POST")
    if (refresh_r.status == 200) {
      r = await httpRequest(url, method, header, body)
    }
  }*/
  return r
}

async function httpRequest(url, method, header, body) {
  return await fetch(url, {
    method: method,
    credentials: "include",
    headers: header,
    body: body
  })
}
