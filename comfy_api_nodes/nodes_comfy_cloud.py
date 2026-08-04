from typing import ClassVar

from typing_extensions import override

from comfy_api.latest import IO, ComfyExtension, Input
from comfy_api_nodes.apis.comfy_cloud import (
    ComfyCloudGenerateRequest,
    ComfyCloudGenerateResponse,
    ComfyCloudStatusResponse,
    ComfyCloudWorkflow,
    ComfyCloudWorkflowInputs,
)
from comfy_api_nodes.util import (
    ApiEndpoint,
    download_url_to_image_tensor,
    download_url_to_video_output,
    get_number_of_images,
    poll_op,
    sync_op,
    upload_image_to_comfyapi,
    validate_string,
)


_GENERATE_ENDPOINT = ApiEndpoint(path="/proxy/comfy-cloud/workflow/generate", method="POST")


class _ComfyCloudWorkflowNode(IO.ComfyNode):
    workflow: ClassVar[ComfyCloudWorkflow]
    node_id: ClassVar[str]
    display_name: ClassVar[str]
    category: ClassVar[str]
    requires_image: ClassVar[bool]
    returns_video: ClassVar[bool]

    @classmethod
    def define_schema(cls) -> IO.Schema:
        inputs = [
            IO.String.Input(
                "prompt",
                multiline=True,
                default="",
                tooltip="Describe the content to generate or the edit to apply.",
            )
        ]
        if cls.requires_image:
            inputs.append(IO.Image.Input("image"))

        output = IO.Video.Output() if cls.returns_video else IO.Image.Output()
        return IO.Schema(
            node_id=cls.node_id,
            display_name=cls.display_name,
            category=cls.category,
            inputs=inputs,
            outputs=[output],
            hidden=[
                IO.Hidden.auth_token_comfy_org,
                IO.Hidden.api_key_comfy_org,
                IO.Hidden.unique_id,
            ],
            is_api_node=True,
        )

    @classmethod
    async def execute(cls, prompt: str, image: Input.Image | None = None) -> IO.NodeOutput:
        validate_string(prompt, min_length=1)

        image_url = None
        if cls.requires_image:
            if get_number_of_images(image) != 1:
                raise ValueError("Exactly one input image is required.")
            image_url = await upload_image_to_comfyapi(cls, image)

        task = await sync_op(
            cls,
            _GENERATE_ENDPOINT,
            response_model=ComfyCloudGenerateResponse,
            data=ComfyCloudGenerateRequest(
                workflow=cls.workflow,
                inputs=ComfyCloudWorkflowInputs(prompt=prompt, image_url=image_url),
            ),
        )
        result = await poll_op(
            cls,
            ApiEndpoint(path=task.polling_url),
            response_model=ComfyCloudStatusResponse,
            status_extractor=lambda response: response.status,
            progress_extractor=lambda response: response.progress,
            cancel_endpoint=ApiEndpoint(path=task.cancel_url, method="POST"),
        )
        if not result.output_url:
            detail = f": {result.error}" if result.error else ""
            raise RuntimeError(f"Comfy Cloud task {result.task_id} completed without an output URL{detail}")

        if cls.returns_video:
            output = await download_url_to_video_output(result.output_url, cls=cls)
        else:
            output = await download_url_to_image_tensor(result.output_url, cls=cls)
        return IO.NodeOutput(output)


class ComfyCloudTextToImageNode(_ComfyCloudWorkflowNode):
    workflow = "text-to-image"
    node_id = "ComfyCloudTextToImageNode"
    display_name = "Comfy Cloud Text to Image"
    category = "partner/image/Comfy Cloud"
    requires_image = False
    returns_video = False


class ComfyCloudTextToVideoNode(_ComfyCloudWorkflowNode):
    workflow = "text-to-video"
    node_id = "ComfyCloudTextToVideoNode"
    display_name = "Comfy Cloud Text to Video"
    category = "partner/video/Comfy Cloud"
    requires_image = False
    returns_video = True


class ComfyCloudImageToVideoNode(_ComfyCloudWorkflowNode):
    workflow = "image-to-video"
    node_id = "ComfyCloudImageToVideoNode"
    display_name = "Comfy Cloud Image to Video"
    category = "partner/video/Comfy Cloud"
    requires_image = True
    returns_video = True


class ComfyCloudImageEditNode(_ComfyCloudWorkflowNode):
    workflow = "image-edit"
    node_id = "ComfyCloudImageEditNode"
    display_name = "Comfy Cloud Image Edit"
    category = "partner/image/Comfy Cloud"
    requires_image = True
    returns_video = False


class ComfyCloudExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[IO.ComfyNode]]:
        return [
            ComfyCloudTextToImageNode,
            ComfyCloudTextToVideoNode,
            ComfyCloudImageToVideoNode,
            ComfyCloudImageEditNode,
        ]


async def comfy_entrypoint() -> ComfyCloudExtension:
    return ComfyCloudExtension()
