function image_and_url(gallery) {
  fetch("http://127.0.0.1:7860/user/")
    .then((response) => response.json())
    .then((data) => (user = data));
  return [extract_image_from_gallery(gallery), user];
}
