# -*- coding: utf-8 -*-


def build_crop(img_w, img_h, crop_center_x, crop_center_y, crop_size):

    shortest_side = min(img_w, img_h)
    crop_size = min(crop_size, shortest_side)

    # closest crop is center + size

    left_half = int(round(crop_size / 2.0))
    right_half = crop_size - left_half

    x1 = crop_center_x - left_half
    x2 = crop_center_x + right_half

    y1 = crop_center_y - left_half
    y2 = crop_center_y + right_half

    # if we have exited the bounds, fix it
    nudge_x = 0
    nudge_y = 0

    if x1 < 0:
        nudge_x = -1 * x1
    elif x2 > img_w:
        nudge_x = -1 * (x2 - img_w)

    if y1 < 0:
        nudge_y = -1 * y1
    elif y2 > img_h:
        nudge_y = -1 * (y2 - img_h)

    if nudge_x or nudge_y:
        return build_crop(img_w, img_h, crop_center_x + nudge_x, crop_center_y + nudge_y, crop_size)

    return (x1, y1, x2, y2)


def build_crops(img_w, img_h, crop_center_x, crop_center_y, crop_size, frames=5):

    shortest_side = min(img_w, img_h)

    zoom_difference = abs(shortest_side - crop_size)
    zoom_per_frame = zoom_difference / float(frames - 1)

    crops = []

    for i in xrange(0, frames):
        zoom_size = shortest_side - int(zoom_per_frame * i)
        crops.append(build_crop(img_w, img_h, crop_center_x, crop_center_y, zoom_size))

    return crops


if __name__ == '__main__':
    print build_crops(200, 300, 50, 75, 25)
    print build_crops(200, 300, 0, 0, 25)
    print build_crops(200, 300, 200, 300, 25)
