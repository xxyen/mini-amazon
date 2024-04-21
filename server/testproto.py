import world_amazon_pb2

def main():
    # Create a new AProduct
    product = world_amazon_pb2.AProduct()
    product.id = 12345
    product.description = "Test product description"
    product.count = 10

    # Serialize the product to a binary string
    product_serialized = product.SerializeToString()
    print("Serialized product:", product_serialized)

    # Deserialize the binary string to a new AProduct object
    product_deserialized = world_amazon_pb2.AProduct()
    product_deserialized.ParseFromString(product_serialized)

    # Print the deserialized content
    print("Deserialized product ID:", product_deserialized.id)
    print("Deserialized product Description:", product_deserialized.description)
    print("Deserialized product Count:", product_deserialized.count)

if __name__ == "__main__":
    main()
