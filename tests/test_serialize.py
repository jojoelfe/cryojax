import pytest

import numpy as np
from jax import config
from dataclasses import replace

import cryojax.simulator as cs
from cryojax.utils import fftn

config.update("jax_enable_x64", True)


def test_deserialize_state_components(noisy_model):
    """Test deserialization on each component of the state."""
    state = noisy_model.state
    pose = cs.EulerPose.from_json(noisy_model.state.pose.to_json())
    ice = cs.GaussianIce.from_json(noisy_model.state.ice.to_json())
    detector = cs.GaussianDetector.from_json(
        noisy_model.state.detector.to_json()
    )
    optics = cs.CTFOptics.from_json(noisy_model.state.optics.to_json())
    exposure = cs.UniformExposure.from_json(
        noisy_model.state.exposure.to_json()
    )
    model = replace(
        noisy_model,
        state=replace(
            state,
            pose=pose,
            detector=detector,
            ice=ice,
            optics=optics,
            exposure=exposure,
        ),
    )
    np.testing.assert_allclose(fftn(noisy_model()), fftn(model()))


def test_deserialize_state(state):
    """Test PipelineState deserialization"""
    assert (
        cs.PipelineState.from_json(state.to_json()).to_json()
        == state.to_json()
    )


def test_deserialize_density(density):
    """Test specimen deserialization."""
    assert (
        cs.ElectronGrid.from_json(density.to_json()).to_json()
        == density.to_json()
    )
    # assert (
    #    ElectronCloud.from_json(cloud.to_json()).to_json() == cloud.to_json()
    # )


@pytest.mark.parametrize("filters_or_masks", ["filters", "masks"])
def test_deserialize_filters_and_masks(filters_or_masks, request):
    """Test model deserialization."""
    filters_or_masks = request.getfixturevalue(filters_or_masks)
    types = [getattr(cs, f.__class__.__name__) for f in filters_or_masks]
    for idx, f in enumerate(filters_or_masks):
        test = types[idx].from_json(f.to_json())
        assert test.to_json() == f.to_json()
        np.testing.assert_allclose(test.evaluate(), f.evaluate(), rtol=1e-6)


@pytest.mark.parametrize(
    "model", ["scattering_model", "optics_model", "noisy_model"]
)
def test_deserialize_model(model, request):
    """Test model deserialization."""
    model = request.getfixturevalue(model)
    cls = getattr(cs, model.__class__.__name__)
    test_model = cls.from_json(model.to_json())
    assert model.to_json() == test_model.to_json()
    np.testing.assert_allclose(test_model(), model(), rtol=1e-6)


def test_serialize_function():
    """Test function serialization as a dataclass field."""

    def f(x):
        return 2 * x

    x = 10
    kernel = cs.Custom(function=f)
    deserialized_kernel = cs.Custom.from_json(kernel.to_json())
    assert kernel(x) == deserialized_kernel(x)
