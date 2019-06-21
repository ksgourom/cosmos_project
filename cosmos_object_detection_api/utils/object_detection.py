import datetime
import os
import numpy as np
import tensorflow as tf
from object_detection.utils import label_map_util
from object_detection.utils import ops as utils_ops

PATH_TO_LABELS = os.path.join(os.getcwd(), 'cosmos_model', 'labelmap.pbtxt')
PATH_TO_GRAPH = os.path.join(os.getcwd(), 'cosmos_model', 'frozen_inference_graph.pb')
GRAPH = None
CATEGORY_INDEX = None


def get_init_graph():
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_GRAPH, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')
    global GRAPH
    GRAPH = detection_graph
    return detection_graph


def get_graph():
    global GRAPH
    return GRAPH if GRAPH is not None else get_init_graph()


def get_init_category_index():
    category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)
    global CATEGORY_INDEX
    CATEGORY_INDEX = category_index
    return category_index


def get_category_index():
    global CATEGORY_INDEX
    return CATEGORY_INDEX if CATEGORY_INDEX is not None else get_init_category_index()


def load_image_as_np_array(image):
    (im_width, im_height) = image.size
    image_np = np.array(image.getdata()).reshape(
        (im_height, im_width, 3)).astype(np.uint8)
    return np.expand_dims(image_np, axis=0)


def run_inference_for_single_image(image, graph):
    with graph.as_default():
        with tf.Session() as sess:
            # Get handles to input and output tensors
            ops = tf.get_default_graph().get_operations()
            all_tensor_names = {output.name for op in ops for output in op.outputs}
            tensor_dict = {}
            for key in [
                'num_detections', 'detection_boxes', 'detection_scores',
                'detection_classes', 'detection_masks'
            ]:
                tensor_name = key + ':0'
                if tensor_name in all_tensor_names:
                    tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(tensor_name)
            if 'detection_masks' in tensor_dict:
                # The following processing is only for single image
                detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
                detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
                # Reframe is required to translate mask from box coordinates to image coordinates
                # and fit the image size.
                real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
                detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
                detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
                detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                    detection_masks, detection_boxes, image.shape[1], image.shape[2])
                detection_masks_reframed = tf.cast(
                    tf.greater(detection_masks_reframed, 0.5), tf.uint8)
                # Follow the convention by adding back the batch dimension
                tensor_dict['detection_masks'] = tf.expand_dims(
                    detection_masks_reframed, 0)
            image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

            # Run inference
            output_dict = sess.run(
                tensor_dict,
                feed_dict={image_tensor: image}
            )

            # all outputs are float32 numpy arrays, so convert types as appropriate
            output_dict['num_detections'] = int(output_dict['num_detections'][0])
            output_dict['detection_classes'] = output_dict[
                'detection_classes'][0].astype(np.int64)
            output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
            output_dict['detection_scores'] = output_dict['detection_scores'][0]
            if 'detection_masks' in output_dict:
                output_dict['detection_masks'] = output_dict['detection_masks'][0]
    return output_dict


def translate(
        classes=None, scores=None,
        category_index=None,
        max_preds=5,
        min_thres=0.5
):
    resp = {}
    for i in range(min(max_preds, len(scores))):
        if scores is None or scores[i] > min_thres:
            cls_name = str(category_index[classes[i]]['name']) if classes[i] in category_index.keys() else "N/A"
            score = "{}%".format(float(100 * scores[i]))
            resp.update(
                {
                    "label": cls_name,
                    "confidence": score
                }
            )
    return resp


def get_predictions(image, verbose=False):
    start = datetime.datetime.now()
    predictions = run_inference_for_single_image(image, get_graph())
    end = datetime.datetime.now() - start
    predictions = translate(
        predictions['detection_classes'],
        predictions['detection_scores'],
        get_category_index(),
    )
    if verbose:
        predictions.update(
            dict(elapsed_time="{} seconds".format(end.total_seconds()))
        )
    return predictions
