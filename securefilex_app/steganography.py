import os
import uuid
from PIL import Image
from django.conf import settings
from django.core.files.storage import default_storage
import numpy as np

DELIMITER = '1111111111111110'  # Unique 16-bit delimiter


def hide_message_in_image(image_file, secret_message):
    try:
        # Load and convert image to RGB
        image = Image.open(image_file).convert('RGB')
        data = np.array(image)
        flat_data = data.flatten()

        # Convert message to binary with delimiter
        binary_message = ''.join(f'{ord(char):08b}' for char in secret_message) + DELIMITER
        binary_bits = np.array(list(map(int, binary_message)), dtype=np.uint8)

        # Check if message fits in image
        if len(binary_bits) > len(flat_data):
            return {
                'message': f'❌ Message too large for this image. Requires {len(binary_bits)} bits, image only supports {len(flat_data)}.',
                'success': False
            }

        # Safe bitwise operations for uint8
        flat_data[:len(binary_bits)] = np.bitwise_and(flat_data[:len(binary_bits)], 254)
        flat_data[:len(binary_bits)] = np.bitwise_or(flat_data[:len(binary_bits)], binary_bits)

        # Reconstruct stego image
        encoded_data = flat_data.reshape(data.shape)
        stego_image = Image.fromarray(encoded_data.astype('uint8'), 'RGB')

        # Save output image
        output_filename = f"stego_{uuid.uuid4().hex}.png"
        output_path = os.path.join(settings.MEDIA_ROOT, output_filename)
        stego_image.save(output_path, format='PNG', optimize=True)

        return {
            'message': '✅ Message successfully hidden in image.',
            'output_image_path': default_storage.url(output_filename),
            'success': True
        }

    except Exception as e:
        return {
            'message': f'❌ Error during encoding: {str(e)}',
            'success': False
        }


def extract_message_from_image(stego_image_file):
    try:
        # Load and convert stego image to flat pixel data
        image = Image.open(stego_image_file).convert('RGB')
        data = np.array(image).flatten()

        # Extract LSBs
        bits = (data & 1).astype(str)
        binary_str = ''.join(bits.tolist())

        # Find delimiter
        delimiter_index = binary_str.find(DELIMITER)
        if delimiter_index == -1:
            return {
                'message': '❌ No hidden message found in image.',
                'success': False
            }

        # Decode binary to string
        message_bits = binary_str[:delimiter_index]
        message = ''.join(
            chr(int(message_bits[i:i + 8], 2)) for i in range(0, len(message_bits), 8)
        )

        return {
            'message': '✅ Message successfully extracted from image.',
            'hidden_text': message,
            'success': True
        }

    except Exception as e:
        return {
            'message': f'❌ Error during decoding: {str(e)}',
            'success': False
        }
